"""
4.4.4 任务 A：资源上传内容校验 / 伪装 / 超限 / 失败清理 / 越权 / 下载一致性。

用法（在 backend 目录）：

    python scripts\\test_444_upload_security.py
"""

from __future__ import annotations

import io
import sys
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


VALID_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _minimal_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


def _fake_zip_as_docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "not a docx")
    return buf.getvalue()


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
    from app.services.resource_write import safe_relative_path, upload_root

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__T444A_{suffix}__"
    created_ids: list[int] = []
    disposable_course_id: int | None = None

    def course_files(course_id: int) -> set[str]:
        d = upload_root() / "courses" / str(course_id)
        if not d.exists():
            return set()
        return {p.name for p in d.iterdir() if p.is_file()}

    def list_tmp_parts() -> set[str]:
        tmp = upload_root() / "_tmp"
        if not tmp.exists():
            return set()
        return {p.name for p in tmp.iterdir() if p.is_file()}

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in created_ids:
                row = db.get(Resource, rid)
                if row:
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
            if disposable_course_id:
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
            other = db.scalar(select(Course).where(Course.teacher_id != int(teacher_id)).limit(1))
            check("other course exists", other is not None)
            other_id = other.id
        finally:
            db.close()

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
        check("create course", r.json().get("code") == 0, str(r.json()))
        disposable_course_id = r.json()["data"]["id"]
        cid = disposable_course_id

        def upload(headers=admin_h, course_id=cid, filename="ok.pdf", content=VALID_PDF, ctype="application/pdf"):
            return client.post(
                "/resource/upload",
                headers=headers,
                files={"file": (filename, io.BytesIO(content), ctype)},
                data={"courseId": str(course_id)},
            )

        # 合法 PDF
        before = course_files(cid)
        r = upload(filename=f"{marker}_ok.pdf")
        check("valid pdf upload", r.json().get("code") == 0, str(r.json()))
        rid = r.json()["data"]["id"]
        created_ids.append(rid)
        check("valid pdf new file", len(course_files(cid) - before) >= 1)

        # 下载一致性
        dl = client.get(f"/resource/{rid}/download", headers=admin_h)
        check("download 200", dl.status_code == 200)
        check("download bytes match", dl.content == VALID_PDF)

        # TXT 改名为 PDF
        before = course_files(cid)
        r = upload(filename=f"{marker}_fake.pdf", content=b"this is plain text not pdf")
        check("txt as pdf rejected", r.json().get("code") == 400, str(r.json()))
        check("txt as pdf no file", course_files(cid) == before)

        # 文本改名为 DOCX
        before = course_files(cid)
        r = upload(
            filename=f"{marker}_fake.docx",
            content=b"plain text pretending to be docx",
            ctype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        check("text as docx rejected", r.json().get("code") == 400, str(r.json()))
        check("text as docx no file", course_files(cid) == before)

        # ZIP 但非 docx 结构
        before = course_files(cid)
        r = upload(filename=f"{marker}_zip.docx", content=_fake_zip_as_docx())
        check("zip as docx rejected", r.json().get("code") == 400)

        # 合法 docx
        r = upload(filename=f"{marker}_ok.docx", content=_minimal_docx_bytes())
        check("valid docx upload", r.json().get("code") == 0, str(r.json()))
        created_ids.append(r.json()["data"]["id"])

        # 扩展名不在白名单
        before = course_files(cid)
        r = upload(filename=f"{marker}.exe", content=b"MZ fake")
        check("exe rejected", r.json().get("code") == 400)
        check("exe no file", course_files(cid) == before)

        # 超过 50MB（临时调小上限）
        with patch.object(settings, "upload_max_bytes", 64):
            before = course_files(cid)
            before_tmp = list_tmp_parts()
            r = upload(filename=f"{marker}_big.pdf", content=VALID_PDF + b"x" * 128)
            check("oversize rejected", r.json().get("code") == 400)
            check("oversize no file", course_files(cid) == before)
            leftover = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
            check("oversize no tmp", leftover == set())

        # DB commit 失败 → 无残留正式文件
        before = course_files(cid)
        before_tmp = list_tmp_parts()
        with patch.object(Session, "commit", side_effect=SQLAlchemyError("boom")):
            r = upload(filename=f"{marker}_dbfail.pdf")
            check("db fail rejected", r.json().get("code") == 500 or r.status_code == 500)
        check("db fail no new file", course_files(cid) == before)
        leftover = {n for n in (list_tmp_parts() - before_tmp) if n.endswith(".part")}
        check("db fail no tmp", leftover == set())

        # 教师跨课程
        before = course_files(other_id)
        r = upload(headers=teacher_h, course_id=other_id, filename=f"{marker}_x.pdf")
        check("teacher cross 403", r.status_code == 403 or r.json().get("code") == 403)
        check("teacher cross no file", course_files(other_id) == before)

        # 教师上传自己课程 OK
        r = upload(headers=teacher_h, course_id=cid, filename=f"{marker}_own.pdf")
        check("teacher own upload", r.json().get("code") == 0, str(r.json()))
        created_ids.append(r.json()["data"]["id"])

        print("[444-upload-security] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
