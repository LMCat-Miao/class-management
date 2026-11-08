"""
4.3.1.3 课程编辑 status 合法性校验。

独立测试课；验证 PUT /course/{id} 仅接受 0/1；未传 status 保持原值；
上下架专用接口行为不变。

用法：

    python scripts\\test_course_update_status_validation.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

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

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.services.course_write import CourseWriteError, normalize_course_status, update_course

    client = TestClient(app)
    marker = f"__TEST_UPD_STATUS_{uuid.uuid4().hex[:8]}__"
    created_id: int | None = None

    def cleanup() -> None:
        if created_id is None:
            return
        db = SessionLocal()
        try:
            row = db.get(Course, created_id)
            if row:
                db.delete(row)
                db.commit()
                print(f"[cleanup] deleted test course id={created_id}")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL] {exc}")
            raise
        finally:
            db.close()

    try:
        # unit: bool must not pass as 0/1
        for bad in (True, False):
            try:
                normalize_course_status(bad)
                check(f"reject bool {bad!r}", False)
            except CourseWriteError as exc:
                check(f"reject bool {bad!r}", exc.status_code == 400)

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
                "duration": 1,
                "status": 1,
                "intro": "status-validation",
            },
        )
        body = r.json()
        check("create fixture", body.get("code") == 0, str(body))
        created_id = body["data"]["id"]
        check("fixture status 1", body["data"].get("status") == 1)

        # 1) status=0
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker, "status": 0},
        )
        check("1 edit status=0 200", r.status_code == 200 and r.json().get("code") == 0)
        check("1 response status 0", r.json()["data"].get("status") == 0)
        db = SessionLocal()
        try:
            check("1 mysql status 0", db.get(Course, created_id).status == 0)
        finally:
            db.close()

        # 2) status=1
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker, "status": 1},
        )
        check("2 edit status=1 200", r.status_code == 200 and r.json().get("code") == 0)
        check("2 response status 1", r.json()["data"].get("status") == 1)

        # 3–5 illegal
        for bad in (2, -1, 999):
            r = client.put(
                f"/course/{created_id}",
                headers=admin_h,
                json={"name": marker, "status": bad},
            )
            check(f"reject status={bad} 400", r.status_code == 400)
            db = SessionLocal()
            try:
                check(f"mysql still 1 after {bad}", db.get(Course, created_id).status == 1)
            finally:
                db.close()

        # service-level defense (bypass schema)
        db = SessionLocal()
        try:
            try:
                update_course(db, created_id, {"status": 2})
                check("service reject 2", False)
            except CourseWriteError as exc:
                check("service reject 2", exc.status_code == 400)
            try:
                update_course(db, created_id, {"status": True})
                check("service reject True", False)
            except CourseWriteError as exc:
                check("service reject True", exc.status_code == 400)
            check("mysql unchanged after service rejects", db.get(Course, created_id).status == 1)
        finally:
            db.close()

        # 6–7 omit status, update other field
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_renamed", "intro": "kept-status"},
        )
        body = r.json()
        check("6 omit status 200", r.status_code == 200 and body.get("code") == 0)
        check("6 name updated", body["data"].get("name") == marker + "_renamed")
        check("7 status still 1", body["data"].get("status") == 1)
        db = SessionLocal()
        try:
            row = db.get(Course, created_id)
            check("7 mysql status still 1", row.status == 1)
            check("7 mysql name updated", row.name == marker + "_renamed")
        finally:
            db.close()

        # 8 teacher 403
        r = client.put(
            f"/course/{created_id}",
            headers=teacher_h,
            json={"name": marker + "_by_teacher", "status": 0},
        )
        check("8 teacher 403", r.status_code == 403)

        # 9 no token 401
        r = client.put(f"/course/{created_id}", json={"name": marker + "_anon"})
        check("9 no token 401", r.status_code == 401)

        # 10 dedicated status endpoint unchanged
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 0},
        )
        check("10 status API 0 ok", r.status_code == 200 and r.json()["data"].get("status") == 0)
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 1},
        )
        check("10 status API 1 ok", r.status_code == 200 and r.json()["data"].get("status") == 1)
        r = client.put(
            f"/course/{created_id}/status",
            headers=admin_h,
            json={"status": 2},
        )
        check("10 status API reject 2", r.status_code == 400)

        print("[course-update-status-validation] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
