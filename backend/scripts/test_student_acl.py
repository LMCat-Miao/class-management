"""
学生管理权限测试（4.3.3 规则）。

- admin：查看全部；可写
- teacher 有档案无选课：空列表
- teacher 有自己课程选课学生：仅可见这些学生
- teacher 不可见其他教师课程学生
- teacher 无档案：403
- teacher 不可新增/编辑/禁用

用法：

    python scripts\\test_student_acl.py
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
    from sqlalchemy import select

    from app.core.security import create_access_token, hash_password
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.student import Student
    from app.models.user import User

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__TEST_STU_ACL_{suffix}__"

    created_student_ids: list[int] = []
    created_enrollment_ids: list[int] = []
    orphan_user_id: int | None = None
    demo_student_nos = {"2025001", "2025002", "2025003", "2025004", "2025005"}

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for eid in created_enrollment_ids:
                row = db.get(Enrollment, eid)
                if row:
                    db.delete(row)
            db.commit()
            for sid in created_student_ids:
                row = db.get(Student, sid)
                if row:
                    db.delete(row)
            db.commit()
            if orphan_user_id is not None:
                u = db.get(User, orphan_user_id)
                if u:
                    db.delete(u)
                    db.commit()
            left = {
                s.student_no
                for s in db.scalars(
                    select(Student).where(Student.student_no.in_(demo_student_nos))
                ).all()
            }
            if left != demo_student_nos:
                print(f"[cleanup][WARN] demo student_no set changed: {left}")
            print("[cleanup] test students/enrollments cleaned")
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
        teacher_id = (tinfo.get("data") or {}).get("teacherId")
        check("teacher has teacherId", teacher_id is not None, str(teacher_id))

        db = SessionLocal()
        try:
            orphan = User(
                username=f"tmp_stu_orphan_{suffix}",
                nickname="无档案学生测",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(orphan)
            db.commit()
            orphan_user_id = orphan.id
            own_course = db.scalar(
                select(Course).where(Course.teacher_id == int(teacher_id)).limit(1)
            )
            other_course = db.scalar(
                select(Course).where(Course.teacher_id != int(teacher_id)).limit(1)
            )
            check("own course exists", own_course is not None)
            check("other course exists", other_course is not None)
            own_course_id = own_course.id
            other_course_id = other_course.id
        finally:
            db.close()

        # 无档案 teacher 不可登录；用签发 Token 验证受保护接口 403
        orphan_login = client.post(
            "/login", json={"username": f"tmp_stu_orphan_{suffix}", "password": "123456"}
        )
        check("orphan login rejected", orphan_login.status_code == 401)
        orphan_h = {
            "Authorization": f"Bearer {create_access_token(orphan_user_id, 'teacher')}"
        }

        # admin list
        r = client.get("/student/list", headers=admin_h, params={"page": 1, "pageSize": 50})
        body = r.json()
        check("admin list 200", r.status_code == 200 and body.get("code") == 0)
        check("admin sees students", body["data"]["total"] >= 1)

        # teacher with profile but no enrollment for marker → empty for marker filter
        # ensure list itself is 200 (may include previously enrolled demo; use dedicated students)
        r = client.get("/student/list", headers=teacher_h, params={"name": marker})
        check(
            "teacher no-enrollment empty for marker",
            r.status_code == 200 and r.json().get("code") == 0 and r.json()["data"]["list"] == [],
        )

        # orphan teacher 403
        r = client.get("/student/list", headers=orphan_h)
        check("orphan teacher list 403", r.status_code == 403)

        # create two students via admin
        r = client.post(
            "/student",
            headers=admin_h,
            json={"name": marker + "_own", "studentNo": f"SA{suffix}", "className": "A"},
        )
        check("admin create own-student", r.status_code == 200 and r.json().get("code") == 0)
        sid_own = r.json()["data"]["id"]
        created_student_ids.append(sid_own)

        r = client.post(
            "/student",
            headers=admin_h,
            json={"name": marker + "_other", "studentNo": f"SB{suffix}", "className": "B"},
        )
        check("admin create other-student", r.status_code == 200 and r.json().get("code") == 0)
        sid_other = r.json()["data"]["id"]
        created_student_ids.append(sid_other)

        # enroll own into teacher's course; other into other teacher's course
        enr = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid_own, "courseId": own_course_id},
        ).json()
        check("enroll own student", enr.get("code") == 0, str(enr.get("message")))
        created_enrollment_ids.append(enr["data"]["id"])

        enr2 = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid_other, "courseId": other_course_id},
        ).json()
        check("enroll other student", enr2.get("code") == 0, str(enr2.get("message")))
        created_enrollment_ids.append(enr2["data"]["id"])

        r = client.get("/student/list", headers=teacher_h, params={"name": marker})
        body = r.json()
        check("teacher list after enroll 200", r.status_code == 200 and body.get("code") == 0)
        ids = {x["id"] for x in body["data"]["list"]}
        check("teacher sees own enrolled student", sid_own in ids)
        check("teacher cannot see other teacher student", sid_other not in ids)

        r = client.get(f"/student/{sid_own}", headers=teacher_h)
        check("teacher detail own 200", r.status_code == 200 and r.json().get("code") == 0)

        r = client.get(f"/student/{sid_other}", headers=teacher_h)
        check("teacher detail other 403", r.status_code == 403)

        r = client.get(f"/student/{sid_own}", headers=admin_h)
        check("admin detail 200", r.status_code == 200)

        r = client.get("/student/99999999", headers=admin_h)
        check("missing student 404", r.status_code == 404)

        # teacher writes forbidden
        payload = {"name": marker + "_x", "className": "测试班", "status": 1}
        r = client.post("/student", headers=teacher_h, json=payload)
        check("teacher create 403", r.status_code == 403)

        r = client.put(f"/student/{sid_own}", headers=teacher_h, json={"name": "hack"})
        check("teacher update 403", r.status_code == 403)

        r = client.put(f"/student/{sid_own}/status", headers=teacher_h, json={"status": 0})
        check("teacher status 403", r.status_code == 403)

        # admin write still works
        r = client.put(
            f"/student/{sid_own}",
            headers=admin_h,
            json={"name": marker + "_edited", "className": "A"},
        )
        check("admin update 200", r.status_code == 200)
        check("name updated", r.json()["data"].get("name") == marker + "_edited")

        r = client.put(f"/student/{sid_own}/status", headers=admin_h, json={"status": 0})
        check("admin status 200", r.status_code == 200)
        check("status 0", r.json()["data"].get("status") == 0)

        r = client.get("/student/list")
        check("no token 401", r.status_code == 401)

        print("[student-acl] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
