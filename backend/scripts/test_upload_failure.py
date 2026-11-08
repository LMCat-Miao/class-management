"""
资源上传故障与事务一致性测试（4.3.3.1）。

模拟方式说明：
- 临时写入失败：mock Path.open 在 _tmp 写入时抛 OSError
- 原子移动失败：mock os.replace 抛 OSError
- 数据库提交失败：mock Session.commit 抛 SQLAlchemyError
其余场景走真实 API / 文件系统。

用法：

    python scripts\\test_upload_failure.py
"""

from __future__ import annotations

import io
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def list_tmp_parts() -> set[str]:
    from app.services.resource_write import upload_root

    tmp = upload_root() / "_tmp"
    if not tmp.exists():
        return set()
    return {p.name for p in tmp.iterdir() if p.is_file()}


def course_files(course_id: int) -> set[str]:
    from app.services.resource_write import upload_root

    d = upload_root() / "courses" / str(course_id)
    if not d.exists():
        return set()
    return {p.name for p in d.iterdir() if p.is_file()}


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    from app.core.config import settings
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.resource import Resource
    from app.services.resource_write import safe_relative_path

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__UPFAIL_{suffix}__"
    created_ids: list[int] = []
    disposable_course_id: int | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in created_ids:
                row = db.get(Resource, rid)
                if not row:
                    continue
                rel = row.file_path
                db.delete(row)
                db.commit()
                if rel:
                    try:
                        p = safe_relative_path(rel)
                        if p.is_file():
                            p.unlink()
                    except Exception:
                        pass
            if disposable_course_id is not None:
                for row in db.scalars(
                    select(Resource).where(Resource.course_id == disposable_course_id)
                ).all():
                    rel = row.file_path
                    db.delete(row)
                    db.commit()
                    if rel:
                        try:
                            p = safe_relative_path(rel)
                            if p.is_file():
                                p.unlink()
                        except Exception:
                            pass
                c = db.get(Course, disposable_course_id)
                if c:
                    db.delete(c)
                    db.commit()
            print("[cleanup] done")
        except Exception as exc:
            db.rollback()
            print(f"[cleanup][WARN] {exc}")
        finally:
            db.close()

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}
        tinfo = client.get("/user/info", headers=teacher_h).json()
        teacher_id = tinfo["data"]["teacherId"]

        db = SessionLocal()
        try:
            own = db.scalar(select(Course).where(Course.teacher_id == int(teacher_id)).limit(1))
            other = db.scalar(select(Course).where(Course.teacher_id != int(teacher_id)).limit(1))
            check("courses exist", own is not None and other is not None)
            own_id, other_id = own.id, other.id
        finally:
            db.close()

        # create disposable course under teacher for isolation
        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": marker,
                "category": "前端",
                "teacherId": teacher_id,
                "duration": 1,
                "status": 1,
            },
        )
        check("create disposable course", r.json().get("code") == 0)
        disposable_course_id = r.json()["data"]["id"]
        cid = disposable_course_id

        # 合法最小 PDF（含 %%EOF）；内容校验后旧的 "%PDF ok" 会失败
        valid_pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"

        def upload(headers=admin_h, course_id: int = cid, filename="ok.pdf", content=valid_pdf):
            return client.post(
                "/resource/upload",
                headers=headers,
                files={"file": (filename, io.BytesIO(content), "application/pdf")},
                data={"courseId": str(course_id)},
            )

        # --- 4) success: DB + file ---
        before_files = course_files(cid)
        before_tmp = list_tmp_parts()
        r = upload(filename=f"{marker}_ok.pdf")
        body = r.json()
        check("success upload", body.get("code") == 0, str(body.get("message")))
        rid = body["data"]["id"]
        created_ids.append(rid)
        db = SessionLocal()
        try:
            row = db.get(Resource, rid)
            check("success db row", row is not None and bool(row.file_path))
            abs_path = safe_relative_path(row.file_path)
            check("success file exists", abs_path.is_file())
        finally:
            db.close()
        check("success no new tmp leftovers", list_tmp_parts() == before_tmp or list_tmp_parts().issuperset(before_tmp) and not (list_tmp_parts() - before_tmp))
        # stricter: no .part from this run left
        leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        check("success no leftover .part", leftover_parts == set())
        check("success new course file", len(course_files(cid) - before_files) >= 1)

        # --- 7) oversize ---
        with patch.object(settings, "upload_max_bytes", 32):
            before_tmp = list_tmp_parts()
            before_files = course_files(cid)
            r = upload(filename=f"{marker}_big.pdf", content=b"x" * 64)
            check("oversize rejected", r.json().get("code") == 400)
            check("oversize no new file", course_files(cid) == before_files)
            leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
            check("oversize no tmp leftover", leftover_parts == set())

        # --- 8) teacher cross-course: deny before file ---
        before_files = course_files(other_id)
        before_tmp = list_tmp_parts()
        r = upload(headers=teacher_h, course_id=other_id, filename=f"{marker}_x.pdf")
        check("teacher cross 403", r.status_code == 403 or r.json().get("code") == 403)
        check("teacher cross no file", course_files(other_id) == before_files)
        leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        check("teacher cross no tmp", leftover_parts == set())

        # --- 1) temp write failure (mock Path.open for .part) ---
        before_tmp = list_tmp_parts()
        before_files = course_files(cid)
        real_open = Path.open

        def open_boom(self, *args, **kwargs):  # noqa: ANN001
            if str(self).endswith(".part") or self.suffix == ".part":
                raise OSError("simulated temp write failure")
            return real_open(self, *args, **kwargs)

        with patch.object(Path, "open", open_boom):
            r = upload(filename=f"{marker}_tmpfail.pdf")
        check("temp write fail → error", r.json().get("code") == 500 or r.status_code >= 400)
        leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        check("temp write fail no leftover .part", leftover_parts == set())
        check("temp write fail no new formal file", course_files(cid) == before_files)

        # --- 2) atomic move failure (mock os.replace) ---
        before_tmp = list_tmp_parts()
        before_files = course_files(cid)
        with patch("app.services.resource_write.os.replace", side_effect=OSError("simulated move fail")):
            r = upload(filename=f"{marker}_movefail.pdf")
        check("move fail → error", r.json().get("code") != 0)
        leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        # move fail: temp may have been consumed or cleaned; formal must not grow
        check("move fail no new formal file", course_files(cid) == before_files)
        check("move fail no leftover .part", leftover_parts == set())

        # --- 3 & 5) DB commit failure → formal file cleaned ---
        before_tmp = list_tmp_parts()
        before_files = course_files(cid)
        from sqlalchemy import func

        db = SessionLocal()
        try:
            db_cnt_before = int(
                db.scalar(select(func.count(Resource.id)).where(Resource.course_id == cid)) or 0
            )
        finally:
            db.close()

        real_commit = Session.commit

        def commit_boom(self):  # noqa: ANN001
            # only boom after a Resource was added in this session
            for obj in list(getattr(self, "new", set()) or []):
                if isinstance(obj, Resource):
                    raise SQLAlchemyError("simulated commit failure")
            return real_commit(self)

        with patch.object(Session, "commit", commit_boom):
            r = upload(filename=f"{marker}_dbfail.pdf")
        check("db commit fail → error", r.json().get("code") == 500 or r.json().get("code") != 0)
        check("db fail no new formal file", course_files(cid) == before_files)
        leftover_parts = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        check("db fail no leftover .part", leftover_parts == set())
        db = SessionLocal()
        try:
            db_cnt_after = int(
                db.scalar(select(func.count(Resource.id)).where(Resource.course_id == cid)) or 0
            )
            check("db fail no new resource row", db_cnt_after == db_cnt_before)
        finally:
            db.close()

        # --- 6) already covered: failures leave no tmp ---
        print("[upload-failure] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
