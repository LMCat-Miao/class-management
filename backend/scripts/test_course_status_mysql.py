"""
4.2.4 课程上下架 MySQL 冒烟测试。

创建专用测试课，验证 status=0/1、非法值、404/403/401、commit 失败不成功；
finally 清理测试课，不改演示数据。

用法：

    python scripts\\test_course_status_mysql.py
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


def cleanup_course(course_id: int | None) -> None:
    if not course_id:
        return
    from app.db.database import SessionLocal
    from app.models.course import Course

    db = SessionLocal()
    try:
        row = db.get(Course, course_id)
        if row:
            db.delete(row)
            db.commit()
            print(f"[cleanup] deleted test course id={course_id}")
        else:
            print(f"[cleanup] course id={course_id} already absent")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"[cleanup][FAIL] residual course id={course_id}: {exc}")
        raise
    finally:
        db.close()


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy.exc import SQLAlchemyError

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.services.course_write import CourseWriteError, update_course_status

    client = TestClient(app)
    created_id: int | None = None
    marker = f"__TEST_STATUS_MYSQL_{uuid.uuid4().hex[:8]}__"

    try:
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
                "intro": "status-test",
            },
        )
        body = r.json()
        check("create fixture", body.get("code") == 0, str(body))
        created_id = body["data"]["id"]
        check("fixture initial status 1", body["data"].get("status") == 1)

        # 1) offline status=0
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 0},
        )
        check("offline 200", r.status_code == 200 and r.json().get("code") == 0)
        check("offline response status 0", r.json()["data"].get("status") == 0)
        check("offline response has id", r.json()["data"].get("id") == created_id)

        # 2) MySQL status=0
        db = SessionLocal()
        try:
            row = db.get(Course, created_id)
            check("mysql status 0", row is not None and row.status == 0)
        finally:
            db.close()

        # 3) online status=1
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 1},
        )
        check("online 200", r.status_code == 200 and r.json().get("code") == 0)
        check("online response status 1", r.json()["data"].get("status") == 1)

        # 4) MySQL status=1
        db = SessionLocal()
        try:
            row = db.get(Course, created_id)
            check("mysql status 1", row is not None and row.status == 1)
        finally:
            db.close()

        # 5) illegal status → 400
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 2},
        )
        check("illegal status 400", r.status_code == 400)
        db = SessionLocal()
        try:
            check("status unchanged after illegal", db.get(Course, created_id).status == 1)
        finally:
            db.close()

        # 6) missing course → 404
        r = client.put(
            "/course/999999/status",
            headers=admin_h,
            json={"status": 0},
        )
        check("missing 404", r.status_code == 404)

        # 7) teacher → 403
        r = client.put(
            f"/course/{created_id}/status",
            headers=teacher_h,
            json={"status": 0},
        )
        check("teacher 403", r.status_code == 403)

        # 8) no token → 401
        r = client.put(f"/course/{created_id}/status", json={"status": 0})
        check("no token 401", r.status_code == 401)

        # 9) commit failure must not succeed / must not change DB
        db = SessionLocal()
        try:
            before = db.get(Course, created_id).status
            with patch.object(db, "commit", side_effect=SQLAlchemyError("boom")):
                try:
                    update_course_status(db, created_id, 0)
                    check("expected write error", False)
                except CourseWriteError as exc:
                    check("commit fail raises CourseWriteError", exc.status_code == 500)
            # refresh after rollback
            db.expire_all()
            after = db.get(Course, created_id).status
            check("mysql unchanged after failed commit", after == before == 1)
        finally:
            db.close()

        print("[course-status-mysql] all checks passed")
        return 0
    finally:
        cleanup_course(created_id)


if __name__ == "__main__":
    raise SystemExit(main())
