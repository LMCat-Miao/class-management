"""
4.3.2.3 教师管理 MySQL 冒烟测试。

用法：

    python scripts\\test_teacher_mysql.py
"""

from __future__ import annotations

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
    from app.models.teacher import Teacher
    from app.services.teacher_write import TeacherWriteError, create_teacher as create_db

    client = TestClient(app)
    marker = f"__TEST_TEACHER_MYSQL_{uuid.uuid4().hex[:8]}__"
    created_teacher_id: int | None = None
    linked_course_id: int | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            if linked_course_id is not None:
                row = db.get(Course, linked_course_id)
                if row:
                    db.delete(row)
                    db.commit()
            if created_teacher_id is not None:
                t = db.get(Teacher, created_teacher_id)
                if t:
                    db.delete(t)
                    db.commit()
                    print(f"[cleanup] deleted teacher id={created_teacher_id}")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL] {exc}")
            raise
        finally:
            db.close()

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}
        teacher_info_id = teacher["data"]["userInfo"].get("teacherId")

        # list
        r = client.get("/teacher/list", headers=admin_h, params={"page": 1, "pageSize": 50})
        body = r.json()
        check("admin list 200", r.status_code == 200 and body.get("code") == 0)
        db = SessionLocal()
        try:
            mysql_cnt = int(db.scalar(select(func.count(Teacher.id))) or 0)
        finally:
            db.close()
        check("list total == mysql", body["data"]["total"] == mysql_cnt)

        # detail seed Zhang (id=1) — stats from MySQL
        r = client.get("/teacher/1", headers=admin_h)
        body = r.json()
        check("detail Zhang 200", r.status_code == 200 and body.get("code") == 0)
        z = body["data"]
        check("detail id is teachers.id", z.get("id") == 1)
        check("teacherId not confused with users.id", teacher_info_id == 1 and z["id"] == 1)
        db = SessionLocal()
        try:
            course_cnt = int(
                db.scalar(select(func.count(Course.id)).where(Course.teacher_id == 1)) or 0
            )
        finally:
            db.close()
        check("courseCount from mysql", z.get("courseCount") == course_cnt)

        # create
        r = client.post(
            "/teacher",
            headers=admin_h,
            json={
                "name": marker,
                "title": "测试讲师",
                "phone": "13900009999",
                "email": "tmp@example.com",
                "status": 1,
            },
        )
        body = r.json()
        check("create 200", r.status_code == 200 and body.get("code") == 0, str(body))
        created_teacher_id = body["data"]["id"]
        check("new id int", isinstance(created_teacher_id, int))
        check("create courseCount 0", body["data"].get("courseCount") == 0)

        # update partial
        r = client.put(
            f"/teacher/{created_teacher_id}",
            headers=admin_h,
            json={"name": marker + "_edited", "title": "高级测试讲师"},
        )
        body = r.json()
        check("update 200", r.status_code == 200)
        check("name edited", body["data"].get("name") == marker + "_edited")
        check("title edited", body["data"].get("title") == "高级测试讲师")

        # delete teacher with courses → 409
        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": marker + "_course",
                "category": "前端",
                "teacherId": created_teacher_id,
                "duration": 1,
            },
        )
        check("link course", r.json().get("code") == 0, str(r.json()))
        linked_course_id = r.json()["data"]["id"]

        r = client.delete(f"/teacher/{created_teacher_id}", headers=admin_h)
        check("delete with courses 409", r.status_code == 409)

        # remove course then delete teacher
        r = client.delete(f"/course/{linked_course_id}", headers=admin_h)
        check("unlink course", r.status_code == 200)
        linked_course_id = None

        r = client.delete(f"/teacher/{created_teacher_id}", headers=admin_h)
        check("delete free teacher 200", r.status_code == 200)
        created_teacher_id = None

        # teacher role 403
        r = client.get("/teacher/list", headers=teacher_h)
        check("teacher list 403", r.status_code == 403)
        r = client.post("/teacher", headers=teacher_h, json={"name": "x"})
        check("teacher create 403", r.status_code == 403)

        r = client.get("/teacher/list")
        check("no token 401", r.status_code == 401)

        # commit failure rollback
        db = SessionLocal()
        try:
            with patch.object(db, "commit", side_effect=SQLAlchemyError("boom")):
                try:
                    from types import SimpleNamespace

                    create_db(
                        db,
                        SimpleNamespace(
                            name=marker + "_fail",
                            avatar="",
                            phone="",
                            email="",
                            title="讲师",
                            status=1,
                        ),
                    )
                    check("expected write error", False)
                except TeacherWriteError as exc:
                    check("commit fail CourseWriteError-like", exc.status_code == 500)
            left = db.scalar(select(Teacher).where(Teacher.name == marker + "_fail"))
            check("no orphan teacher after fail", left is None)
        finally:
            db.close()

        print("[teacher-mysql] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
