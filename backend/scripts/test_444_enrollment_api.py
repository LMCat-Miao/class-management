"""
4.4.4 任务 C：选课 API 权限与业务闭环（独立测试数据）。

用法（在 backend 目录）：

    python scripts\\test_444_enrollment_api.py
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


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.student import Student

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__T444E_{suffix}__"
    student_ids: list[int] = []
    enrollment_ids: list[int] = []

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for eid in enrollment_ids:
                row = db.get(Enrollment, eid)
                if row:
                    db.delete(row)
            db.commit()
            for sid in student_ids:
                row = db.get(Student, sid)
                if row:
                    db.delete(row)
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

        db = SessionLocal()
        try:
            course = db.scalar(select(Course).limit(1))
            check("course exists", course is not None)
            course_id = course.id
        finally:
            db.close()

        created = client.post(
            "/student",
            headers=admin_h,
            json={"name": marker, "studentNo": f"E444{suffix}", "className": "E"},
        ).json()
        check("create student", created.get("code") == 0)
        sid = created["data"]["id"]
        student_ids.append(sid)

        # teacher 禁止选课操作
        r = client.post(
            "/enrollment",
            headers=teacher_h,
            json={"studentId": sid, "courseId": course_id},
        )
        check("teacher create 403", r.status_code == 403 or r.json().get("code") == 403)

        r = client.get(f"/enrollment/student/{sid}", headers=teacher_h)
        check("teacher list 403", r.status_code == 403 or r.json().get("code") == 403)

        # admin 创建
        enr = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        check("admin enroll", enr.get("code") == 0, str(enr))
        eid = enr["data"]["id"]
        enrollment_ids.append(eid)
        check("status active", enr["data"]["status"] == 1)
        check("fields", "courseName" in enr["data"] and "studentId" in enr["data"])

        # 重复有效选课
        dup = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        check("dup rejected", dup.get("code") == 400)

        lst = client.get(f"/enrollment/student/{sid}", headers=admin_h).json()
        check("list ok", lst.get("code") == 0 and len(lst["data"]) >= 1)

        # 退选
        dropped = client.put(f"/enrollment/{eid}/drop", headers=admin_h).json()
        check("drop ok", dropped.get("code") == 0 and dropped["data"]["status"] == 0)

        # 再次选课恢复同一记录
        again = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        check("re-enroll ok", again.get("code") == 0 and again["data"]["status"] == 1)
        check("re-enroll same id", again["data"]["id"] == eid)

        # teacher 退选禁止
        r = client.put(f"/enrollment/{eid}/drop", headers=teacher_h)
        check("teacher drop 403", r.status_code == 403 or r.json().get("code") == 403)

        print("[444-enrollment-api] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
