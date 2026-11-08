"""
4.4.3 列表 SQL 分页 / enrollment JOIN / 错误码 / 账号停用标识。

独立测试数据，try/finally 清理；不改演示账号。

用法：

    python scripts\\test_443_paging_api.py
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

    from app.core.security import create_access_token, hash_password
    from app.db.database import SessionLocal, engine
    from app.main import app
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.resource import Resource
    from app.models.student import Student
    from app.models.teacher import Teacher
    from app.models.user import User
    from app.services import enrollment_service

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__T443_{suffix}__"

    student_ids: list[int] = []
    enrollment_ids: list[int] = []
    teacher_ids: list[int] = []
    user_ids: list[int] = []
    resource_ids: list[int] = []
    course_ids: list[int] = []

    def cleanup() -> None:
        db = SessionLocal()
        try:
            from app.services.resource_write import safe_relative_path

            for rid in resource_ids:
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
            db.commit()
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
            for cid in course_ids:
                row = db.get(Course, cid)
                if row:
                    db.delete(row)
            db.commit()
            for tid in teacher_ids:
                row = db.get(Teacher, tid)
                if row:
                    db.delete(row)
            db.commit()
            for uid in user_ids:
                row = db.get(User, uid)
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

        # ---- API error code alignment ----
        r = client.post("/login", json={"username": "admin", "password": "bad"})
        check("401 http", r.status_code == 401)
        check("401 body.code==401", r.json().get("code") == 401)

        r = client.get("/student/99999999", headers=admin_h)
        check("404 body.code==404", r.status_code == 404 and r.json().get("code") == 404)

        r = client.post("/student", headers=admin_h, json={})
        check("422 http", r.status_code == 422)
        check("422 body.code==422", r.json().get("code") == 422)
        check("422 no errors leak", "errors" not in r.json())

        # ---- create disposable teachers for paging ----
        db = SessionLocal()
        try:
            for i in range(3):
                u = User(
                    username=f"tmp_443_t{i}_{suffix}",
                    nickname=f"t{i}",
                    password_hash=hash_password("123456"),
                    role="teacher",
                )
                db.add(u)
                db.flush()
                user_ids.append(u.id)
                t = Teacher(
                    user_id=u.id,
                    name=f"{marker}_T{i}",
                    status=1 if i < 2 else 0,
                    title="讲师",
                )
                db.add(t)
                db.flush()
                teacher_ids.append(t.id)
            db.commit()
        finally:
            db.close()

        # teacher list page
        r = client.get(
            "/teacher/list",
            headers=admin_h,
            params={"name": marker, "page": 1, "pageSize": 2},
        ).json()
        check("teacher page1", r.get("code") == 0)
        check("teacher page1 size<=2", len(r["data"]["list"]) <= 2)
        check("teacher total>=3", r["data"]["total"] >= 3)
        page1_ids = [x["id"] for x in r["data"]["list"]]

        r2 = client.get(
            "/teacher/list",
            headers=admin_h,
            params={"name": marker, "page": 2, "pageSize": 2},
        ).json()
        page2_ids = [x["id"] for x in r2["data"]["list"]]
        check("teacher page2 disjoint", set(page1_ids).isdisjoint(page2_ids) or r2["data"]["total"] <= 2)
        r3 = client.get(
            "/teacher/list",
            headers=admin_h,
            params={"name": marker, "page": 99, "pageSize": 2},
        ).json()
        check("teacher overflow empty list", r3["data"]["list"] == [])
        r_st = client.get(
            "/teacher/list",
            headers=admin_h,
            params={"name": marker, "status": "0", "page": 1, "pageSize": 10},
        ).json()
        check(
            "teacher status filter",
            r_st.get("code") == 0 and all(x["status"] == 0 for x in r_st["data"]["list"]),
        )

        # ---- students paging + teacher ACL ----
        teacher_login = client.post(
            "/login", json={"username": "teacher", "password": "123456"}
        ).json()
        teacher_h = {"Authorization": f"Bearer {teacher_login['data']['accessToken']}"}
        tinfo = client.get("/user/info", headers=teacher_h).json()
        demo_tid = tinfo["data"]["teacherId"]

        db = SessionLocal()
        try:
            own_course = db.scalar(select(Course).where(Course.teacher_id == demo_tid).limit(1))
            other_course = db.scalar(select(Course).where(Course.teacher_id != demo_tid).limit(1))
            check("courses exist", own_course is not None and other_course is not None)
            own_cid, other_cid = own_course.id, other_course.id
        finally:
            db.close()

        created = []
        for i in range(5):
            body = client.post(
                "/student",
                headers=admin_h,
                json={"name": f"{marker}_S{i}", "studentNo": f"P443{suffix}{i}", "className": "P"},
            ).json()
            check(f"create student {i}", body.get("code") == 0)
            sid = body["data"]["id"]
            student_ids.append(sid)
            created.append(sid)

        # enroll first 3 into own course; also enroll #0 into second own course if any to test distinct
        for sid in created[:3]:
            enr = client.post(
                "/enrollment",
                headers=admin_h,
                json={"studentId": sid, "courseId": own_cid},
            ).json()
            check("enroll", enr.get("code") == 0)
            enrollment_ids.append(enr["data"]["id"])

        # student #3 into other teacher course only
        enr = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": created[3], "courseId": other_cid},
        ).json()
        check("enroll other", enr.get("code") == 0)
        enrollment_ids.append(enr["data"]["id"])

        # duplicate course enroll path: second course of same teacher if available
        db = SessionLocal()
        try:
            second = db.scalar(
                select(Course)
                .where(Course.teacher_id == demo_tid, Course.id != own_cid)
                .limit(1)
            )
            second_cid = second.id if second else None
        finally:
            db.close()
        if second_cid:
            enr = client.post(
                "/enrollment",
                headers=admin_h,
                json={"studentId": created[0], "courseId": second_cid},
            ).json()
            if enr.get("code") == 0:
                enrollment_ids.append(enr["data"]["id"])

        r = client.get(
            "/student/list",
            headers=admin_h,
            params={"name": marker, "page": 1, "pageSize": 2},
        ).json()
        check("admin student page1", r.get("code") == 0 and len(r["data"]["list"]) == 2)
        check("admin student total 5", r["data"]["total"] == 5)
        r = client.get(
            "/student/list",
            headers=admin_h,
            params={"name": marker, "page": 3, "pageSize": 2},
        ).json()
        check("admin student page3 size1", len(r["data"]["list"]) == 1)

        r = client.get(
            "/student/list",
            headers=teacher_h,
            params={"name": marker, "page": 1, "pageSize": 10},
        ).json()
        check("teacher student list ok", r.get("code") == 0)
        ids = [x["id"] for x in r["data"]["list"]]
        check("teacher sees enrolled own", created[0] in ids and created[1] in ids and created[2] in ids)
        check("teacher no other-course-only student", created[3] not in ids)
        check("teacher no unenrolled", created[4] not in ids)
        check("teacher no duplicate students", len(ids) == len(set(ids)))

        # ---- resources paging ----
        # upload a few small pdfs to own course
        import io

        for i in range(3):
            up = client.post(
                "/resource/upload",
                headers=admin_h,
                data={"courseId": str(own_cid)},
                files={
                    "file": (
                        f"{marker}_{i}.pdf",
                        io.BytesIO(
                            b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + str(i).encode()
                        ),
                        "application/pdf",
                    )
                },
            ).json()
            check(f"upload res {i}", up.get("code") == 0)
            resource_ids.append(up["data"]["id"])

        r = client.get(
            "/resource/list",
            headers=admin_h,
            params={"courseId": own_cid, "name": marker, "page": 1, "pageSize": 2},
        ).json()
        check("resource page1", r.get("code") == 0 and len(r["data"]["list"]) == 2)
        check("resource total>=3", r["data"]["total"] >= 3)
        r = client.get(
            "/resource/list",
            headers=teacher_h,
            params={"name": marker, "page": 1, "pageSize": 50},
        ).json()
        check("teacher resource list", r.get("code") == 0)
        check("teacher resource non-empty", len(r["data"]["list"]) >= 3)
        check(
            "teacher only own course resources",
            all(x["courseId"] == own_cid for x in r["data"]["list"]),
        )

        # ---- enrollment JOIN：统计实际 SQL 次数（优化后应为「存在性 + JOIN 列表」量级）----
        from sqlalchemy import event as sa_event

        q2: list[str] = []

        def _count_sql(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            q2.append(statement)

        sa_event.listen(engine, "before_cursor_execute", _count_sql)
        db = SessionLocal()
        try:
            q2.clear()
            items = enrollment_service.list_enrollments_for_student(db, created[0])
            after_join = len(q2)
            check("enrollment list type", isinstance(items, list))
            check(
                "enrollment student list queries low",
                after_join <= 4,
                f"queries={after_join} sqls={q2!r}",
            )
            q2.clear()
            items2 = enrollment_service.list_enrollments_for_course(db, own_cid)
            after2 = len(q2)
            check(
                "enrollment course list queries low",
                after2 <= 4,
                f"queries={after2}",
            )
            check(
                "enrollment fields",
                all("studentId" in x and "courseId" in x for x in items2),
            )
        finally:
            sa_event.remove(engine, "before_cursor_execute", _count_sql)
            db.close()

        # ---- ACCOUNT_DISABLED error code ----
        db = SessionLocal()
        try:
            u = User(
                username=f"tmp_443_dis_{suffix}",
                nickname="dis",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(u)
            db.flush()
            user_ids.append(u.id)
            t = Teacher(user_id=u.id, name=f"{marker}_DIS", status=1, title="讲师")
            db.add(t)
            db.flush()
            teacher_ids.append(t.id)
            db.commit()
            uid, tid = u.id, t.id
        finally:
            db.close()

        login = client.post(
            "/login", json={"username": f"tmp_443_dis_{suffix}", "password": "123456"}
        ).json()
        check("temp teacher login", login.get("code") == 0)
        tok = login["data"]["accessToken"]
        h = {"Authorization": f"Bearer {tok}"}

        db = SessionLocal()
        try:
            t = db.get(Teacher, tid)
            t.status = 0
            db.commit()
        finally:
            db.close()

        r = client.get("/user/info", headers=h)
        check("disabled 403", r.status_code == 403)
        check("disabled error=ACCOUNT_DISABLED", r.json().get("error") == "ACCOUNT_DISABLED")
        check("disabled body.code=403", r.json().get("code") == 403)

        # ordinary 403 still no ACCOUNT_DISABLED (teacher accessing admin teacher list)
        r = client.get("/teacher/list", headers=teacher_h)
        check("ordinary teacher 403", r.status_code == 403)
        check("ordinary 403 no ACCOUNT_DISABLED", r.json().get("error") != "ACCOUNT_DISABLED")

        print("[443-paging-api] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
