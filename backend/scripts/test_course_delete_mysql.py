"""
课程删除 MySQL 测试（含 4.3.3 资源元数据 + 文件清理）。

- 创建专用测试课程 + MySQL 资源（含落盘文件）；不删演示课/演示资源。
- finally 中兜底清理。

用法：

    python scripts\\test_course_delete_mysql.py
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


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select
    from sqlalchemy.exc import SQLAlchemyError

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.resource import Resource
    from app.services.course_write import CourseWriteError, delete_course as delete_course_db
    from app.services.resource_write import safe_relative_path

    client = TestClient(app)
    created_id: int | None = None
    resource_ids: list[int] = []
    file_paths: list[str] = []
    marker = f"__TEST_DELETE_MYSQL_{uuid.uuid4().hex[:8]}__"
    demo_null_path_before: int | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in list(resource_ids):
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
            if created_id is not None:
                for row in db.scalars(
                    select(Resource).where(Resource.course_id == created_id)
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
                row = db.get(Course, created_id)
                if row:
                    db.delete(row)
                    db.commit()
                    print(f"[cleanup] residual course id={created_id} removed")
            for rel in file_paths:
                try:
                    p = safe_relative_path(rel)
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL]: {exc}")
        finally:
            db.close()

    try:
        db = SessionLocal()
        try:
            demo_null_path_before = int(
                db.scalar(
                    select(func.count(Resource.id)).where(Resource.file_path.is_(None))
                )
                or 0
            )
        finally:
            db.close()

        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}

        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": marker,
                "category": "前端",
                "teacherId": 1,
                "difficulty": "初级",
                "duration": 1,
                "status": 1,
                "intro": "delete-test",
            },
        )
        body = r.json()
        check("create fixture", body.get("code") == 0, str(body))
        created_id = body["data"]["id"]

        up = client.post(
            "/resource/upload",
            headers=admin_h,
            files={
                "file": (
                    f"{marker}.pdf",
                    io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\ndelete\n"),
                    "application/pdf",
                )
            },
            data={"courseId": str(created_id)},
        ).json()
        check("upload fixture resource", up.get("code") == 0, str(up.get("message")))
        test_resource_id = up["data"]["id"]
        resource_ids.append(test_resource_id)

        db = SessionLocal()
        try:
            row = db.get(Resource, test_resource_id)
            check("resource row exists", row is not None and bool(row.file_path))
            rel = row.file_path
            file_paths.append(rel)
            abs_path = safe_relative_path(rel)
            check("resource file exists", abs_path.is_file())
            other_resources_before = int(
                db.scalar(
                    select(func.count(Resource.id)).where(Resource.id != test_resource_id)
                )
                or 0
            )
        finally:
            db.close()

        r = client.delete(f"/course/{created_id}", headers=admin_h)
        check("admin delete 200", r.status_code == 200 and r.json().get("code") == 0)
        check("delete data True", r.json().get("data") is True)

        db = SessionLocal()
        try:
            check("mysql course removed", db.get(Course, created_id) is None)
            check("mysql resource purged", db.get(Resource, test_resource_id) is None)
            other_after = int(
                db.scalar(
                    select(func.count(Resource.id)).where(Resource.id != test_resource_id)
                )
                or 0
            )
            # test id gone so count of "others" should match previous others
            check("other resources kept", other_after == other_resources_before)
            null_after = int(
                db.scalar(
                    select(func.count(Resource.id)).where(Resource.file_path.is_(None))
                )
                or 0
            )
            check(
                "demo null-path resources intact",
                null_after >= (demo_null_path_before or 0),
                f"before={demo_null_path_before} after={null_after}",
            )
        finally:
            db.close()
        check("disk file cleaned", not abs_path.exists())
        resource_ids = [x for x in resource_ids if x != test_resource_id]
        created_id = None

        r = client.delete("/course/999999", headers=admin_h)
        check("missing 404", r.status_code == 404)

        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": marker + "_forbid",
                "category": "前端",
                "teacherId": 1,
                "duration": 1,
            },
        )
        check("create for 403 test", r.json().get("code") == 0)
        forbid_id = r.json()["data"]["id"]
        created_id = forbid_id

        r = client.delete(f"/course/{forbid_id}", headers=teacher_h)
        check("teacher delete 403", r.status_code == 403)
        db = SessionLocal()
        try:
            check("course remains after 403", db.get(Course, forbid_id) is not None)
        finally:
            db.close()

        r = client.delete(f"/course/{forbid_id}")
        check("no token 401", r.status_code == 401)

        # commit failure must not remove course / resources
        up2 = client.post(
            "/resource/upload",
            headers=admin_h,
            files={
                "file": (
                    f"{marker}_fail.pdf",
                    io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\nfail\n"),
                    "application/pdf",
                )
            },
            data={"courseId": str(forbid_id)},
        ).json()
        check("upload for commit-fail case", up2.get("code") == 0)
        fail_rid = up2["data"]["id"]
        resource_ids.append(fail_rid)
        db = SessionLocal()
        try:
            fail_rel = db.get(Resource, fail_rid).file_path
            file_paths.append(fail_rel)
            fail_abs = safe_relative_path(fail_rel)
            with patch.object(db, "commit", side_effect=SQLAlchemyError("boom")):
                try:
                    delete_course_db(db, forbid_id)
                    check("expected write error", False)
                except CourseWriteError as exc:
                    check("commit fail raises CourseWriteError", exc.status_code == 500)
            check("resource not purged on failed delete", db.get(Resource, fail_rid) is not None)
            check("course still in mysql after failed delete", db.get(Course, forbid_id) is not None)
            check("file kept after failed delete", fail_abs.is_file())
        finally:
            db.close()

        r = client.delete(f"/course/{forbid_id}", headers=admin_h)
        check("cleanup delete forbid course", r.status_code == 200)
        check("file cleaned after real delete", not fail_abs.exists())
        created_id = None
        resource_ids = [x for x in resource_ids if x not in (fail_rid,)]

        print("[course-delete-mysql] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
