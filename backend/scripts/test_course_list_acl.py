"""
4.3.1.2 课程列表 ACL：无教师档案 teacher 不得看到全量课程。

独立测试用户/教师/课程；finally 清理；不改演示账号与演示课。

用法：

    python scripts\\test_course_list_acl.py
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

    from app.core.security import create_access_token, hash_password
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.teacher import Teacher
    from app.models.user import User
    from app.services.course_query import CourseQueryError, list_courses_page, parse_list_teacher_id

    client = TestClient(app)
    marker = f"__TEST_LIST_ACL_{uuid.uuid4().hex[:8]}__"
    suffix = uuid.uuid4().hex[:8]

    course_a_id: int | None = None
    course_b_id: int | None = None
    teacher_b_id: int | None = None
    user_b_id: int | None = None
    orphan_user_id: int | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for cid in (course_a_id, course_b_id):
                if cid is None:
                    continue
                row = db.get(Course, cid)
                if row:
                    db.delete(row)
            db.commit()
            if teacher_b_id is not None:
                t = db.get(Teacher, teacher_b_id)
                if t:
                    db.delete(t)
            for uid in (user_b_id, orphan_user_id):
                if uid is None:
                    continue
                u = db.get(User, uid)
                if u:
                    db.delete(u)
            db.commit()
            print("[cleanup] mysql test users/teachers/courses removed")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL] {exc}")
            raise
        finally:
            db.close()

    try:
        # unit: parse_list_teacher_id
        check("parse None", parse_list_teacher_id(None) is None)
        check("parse empty", parse_list_teacher_id("") is None)
        check("parse blank", parse_list_teacher_id("  ") is None)
        check("parse zero", parse_list_teacher_id(0) is None)
        check("parse neg", parse_list_teacher_id(-1) is None)
        check("parse bad", parse_list_teacher_id("x") is None)
        check("parse ok int", parse_list_teacher_id(3) == 3)
        check("parse ok str", parse_list_teacher_id("7") == 7)

        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher_a = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher A login", teacher_a.get("code") == 0)
        teacher_a_h = {"Authorization": f"Bearer {teacher_a['data']['accessToken']}"}
        teacher_a_id = teacher_a["data"]["userInfo"]["teacherId"]
        check("teacher A teacherId", isinstance(teacher_a_id, int) and teacher_a_id > 0)

        db = SessionLocal()
        try:
            ub = User(
                username=f"tmp_list_tb_{suffix}",
                nickname=f"列表教师B_{suffix}",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(ub)
            db.flush()
            user_b_id = ub.id
            tb = Teacher(
                user_id=ub.id,
                name=f"列表教师B_{suffix}",
                avatar="",
                phone="",
                email="",
                title="讲师",
                status=1,
            )
            db.add(tb)
            db.flush()
            teacher_b_id = tb.id

            orphan = User(
                username=f"tmp_list_orphan_{suffix}",
                nickname=f"无档案列表_{suffix}",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(orphan)
            db.flush()
            orphan_user_id = orphan.id
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        teacher_b = client.post(
            "/login", json={"username": f"tmp_list_tb_{suffix}", "password": "123456"}
        ).json()
        check("teacher B login", teacher_b.get("code") == 0)
        teacher_b_h = {"Authorization": f"Bearer {teacher_b['data']['accessToken']}"}
        check(
            "teacher B teacherId",
            teacher_b["data"]["userInfo"].get("teacherId") == teacher_b_id,
        )

        orphan_login = client.post(
            "/login", json={"username": f"tmp_list_orphan_{suffix}", "password": "123456"}
        )
        check("orphan login rejected", orphan_login.status_code == 401)
        orphan_h = {
            "Authorization": f"Bearer {create_access_token(orphan_user_id, 'teacher')}"
        }

        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": f"{marker}_A",
                "category": "前端",
                "teacherId": teacher_a_id,
                "duration": 1,
                "status": 1,
            },
        )
        check("create course A", r.json().get("code") == 0, str(r.json()))
        course_a_id = r.json()["data"]["id"]

        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": f"{marker}_B",
                "category": "前端",
                "teacherId": teacher_b_id,
                "duration": 1,
                "status": 1,
            },
        )
        check("create course B", r.json().get("code") == 0, str(r.json()))
        course_b_id = r.json()["data"]["id"]

        # 1–2 admin
        r = client.get("/course/list", headers=admin_h, params={"page": 1, "pageSize": 100})
        body = r.json()
        check("1 admin list 200", r.status_code == 200 and body.get("code") == 0)
        admin_ids = {x["id"] for x in body["data"]["list"]}
        check("2 admin sees A and B", course_a_id in admin_ids and course_b_id in admin_ids)

        # 3–5 teacher A
        r = client.get("/course/list", headers=teacher_a_h, params={"page": 1, "pageSize": 100})
        body = r.json()
        check("3 teacher A list 200", r.status_code == 200 and body.get("code") == 0)
        a_list = body["data"]["list"]
        check("4 only own teacherId", all(x.get("teacherId") == teacher_a_id for x in a_list))
        a_ids = {x["id"] for x in a_list}
        check("4 has course A", course_a_id in a_ids)
        check("5 no course B", course_b_id not in a_ids)

        # 6 filter bypass attempt: search by B's name / teacher name
        r = client.get(
            "/course/list",
            headers=teacher_a_h,
            params={"name": f"{marker}_B", "page": 1, "pageSize": 50},
        )
        body = r.json()
        check("6 name filter still scoped", r.status_code == 200 and body.get("code") == 0)
        check("6 cannot see B via name", all(x.get("id") != course_b_id for x in body["data"]["list"]))
        check("6 total not leaking B", body["data"]["total"] == 0 or course_b_id not in {
            x["id"] for x in body["data"]["list"]
        })

        r = client.get(
            "/course/list",
            headers=teacher_a_h,
            params={"teacher": f"列表教师B_{suffix}", "page": 1, "pageSize": 50},
        )
        body = r.json()
        check("6 teacher-name filter scoped", r.status_code == 200)
        check(
            "6 cannot see B via teacher param",
            course_b_id not in {x["id"] for x in body["data"]["list"]},
        )

        # 7–9 orphan teacher
        r = client.get("/course/list", headers=orphan_h, params={"page": 1, "pageSize": 10})
        body = r.json()
        check("7 orphan list 403", r.status_code == 403)
        check("8 orphan no data", body.get("data") is None)
        check("8 orphan message", bool(body.get("message")))

        # service-level: missing teacherId must raise before query
        db = SessionLocal()
        try:
            try:
                list_courses_page(db, user={"role": "teacher"})
                check("9 service raises without teacherId", False)
            except CourseQueryError as exc:
                check("9 CourseQueryError 403", exc.status_code == 403)
            try:
                list_courses_page(db, user={"role": "teacher", "teacherId": ""})
                check("9 empty teacherId raises", False)
            except CourseQueryError as exc:
                check("9 empty teacherId 403", exc.status_code == 403)
            try:
                list_courses_page(db, user={"role": "teacher", "teacherId": "abc"})
                check("9 invalid teacherId raises", False)
            except CourseQueryError as exc:
                check("9 invalid teacherId 403", exc.status_code == 403)
        finally:
            db.close()

        # 10–11 auth
        r = client.get("/course/list")
        check("10 no token 401", r.status_code == 401)
        r = client.get("/course/list", headers={"Authorization": "Bearer not-a-jwt"})
        check("11 invalid token 401", r.status_code == 401)

        print("[course-list-acl] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
