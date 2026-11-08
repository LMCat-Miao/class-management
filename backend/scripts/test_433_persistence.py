"""
4.3.3 学生/选课/资源持久化集成回归。

用法（backend 目录、venv）：

    python scripts\\test_433_persistence.py

使用独立测试数据，try/finally 清理；不删除演示数据。
"""

from __future__ import annotations

import io
import sys
import uuid
import zipfile
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
        raise AssertionError(name)


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select, text

    from app.core.security import create_access_token, hash_password
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.resource import Resource
    from app.models.student import Student
    from app.models.teacher import Teacher
    from app.models.user import User
    from app.services.resource_write import safe_relative_path, upload_root

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__T433_{suffix}__"

    created_student_ids: list[int] = []
    created_enrollment_ids: list[int] = []
    created_resource_ids: list[int] = []
    created_course_ids: list[int] = []
    orphan_user_id: int | None = None
    orphan_teacher_id: int | None = None
    fail_count = 0

    def try_check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal fail_count
        try:
            check(name, cond, detail)
        except AssertionError:
            fail_count += 1

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in created_resource_ids:
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
            for cid in created_course_ids:
                # 先清该课资源与选课
                for r in db.scalars(select(Resource).where(Resource.course_id == cid)).all():
                    rel = r.file_path
                    db.delete(r)
                    db.commit()
                    if rel:
                        try:
                            p = safe_relative_path(rel)
                            if p.is_file():
                                p.unlink()
                        except Exception:
                            pass
                for e in db.scalars(select(Enrollment).where(Enrollment.course_id == cid)).all():
                    db.delete(e)
                    db.commit()
                c = db.get(Course, cid)
                if c:
                    db.delete(c)
                    db.commit()
            if orphan_teacher_id is not None:
                t = db.get(Teacher, orphan_teacher_id)
                if t:
                    db.delete(t)
                    db.commit()
            if orphan_user_id is not None:
                u = db.get(User, orphan_user_id)
                if u:
                    db.delete(u)
                    db.commit()
        except Exception as exc:
            db.rollback()
            print(f"[cleanup][WARN] {exc}")
        finally:
            db.close()
        print("[cleanup] done")

    try:
        # ---- baseline demo counts ----
        db = SessionLocal()
        try:
            base_users = db.scalar(select(func.count(User.id)))
            base_teachers = db.scalar(select(func.count(Teacher.id)))
            base_courses = db.scalar(select(func.count(Course.id)))
            base_cats = db.execute(text("SELECT COUNT(*) FROM course_categories")).scalar()
            head = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
        finally:
            db.close()
        try_check("alembic head", head == "20260323_0001", str(head))

        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        try_check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        try_check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}
        tinfo = client.get("/user/info", headers=teacher_h).json()
        try_check("teacher /user/info", tinfo.get("code") == 0)
        teacher_id = (tinfo.get("data") or {}).get("teacherId")
        try_check("teacher has teacherId", teacher_id is not None, str(teacher_id))
        if teacher_id is None:
            raise SystemExit("teacherId missing; abort remaining teacher ACL cases")

        # orphan teacher user (no teachers row)
        db = SessionLocal()
        try:
            ou = User(
                username=f"tmp_orphan_{suffix}",
                nickname="orphan",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(ou)
            db.commit()
            db.refresh(ou)
            orphan_user_id = ou.id
        finally:
            db.close()
        orphan_login = client.post(
            "/login", json={"username": f"tmp_orphan_{suffix}", "password": "123456"}
        )
        try_check("orphan teacher login rejected", orphan_login.status_code == 401)
        orphan_h = {
            "Authorization": f"Bearer {create_access_token(orphan_user_id, 'teacher')}"
        }

        # ---- student CRUD admin ----
        create = client.post(
            "/student",
            headers=admin_h,
            json={
                "name": marker,
                "studentNo": f"T433{suffix}",
                "className": "测试班",
                "phone": "13900009999",
                "status": 1,
            },
        ).json()
        try_check("admin create student", create.get("code") == 0, str(create.get("message")))
        sid = create["data"]["id"]
        created_student_ids.append(sid)
        try_check("studentNo mapped", create["data"]["studentNo"] == f"T433{suffix}")
        try_check("recentCourses default []", create["data"]["recentCourses"] == [])
        try_check("stats default 0", create["data"]["learnCourseCount"] == 0)

        dup = client.post(
            "/student",
            headers=admin_h,
            json={"name": "dup", "studentNo": f"T433{suffix}"},
        ).json()
        try_check("duplicate studentNo rejected", dup.get("code") != 0 and dup.get("code") != 500)

        bad_prog = client.put(
            f"/student/{sid}",
            headers=admin_h,
            json={"name": marker, "progress": 101},
        ).json()
        try_check("progress>100 rejected", bad_prog.get("code") == 400)

        bad_st = client.put(
            f"/student/{sid}/status",
            headers=admin_h,
            json={"status": 2},
        ).json()
        try_check("illegal status rejected", bad_st.get("code") == 400)

        # partial update: omit phone — must keep
        prev_phone = create["data"]["phone"]
        upd = client.put(
            f"/student/{sid}",
            headers=admin_h,
            json={"name": marker + "_u", "className": "测试班2"},
        ).json()
        try_check("partial update ok", upd.get("code") == 0)
        try_check("phone preserved", upd["data"]["phone"] == prev_phone)
        try_check("name updated", upd["data"]["name"] == marker + "_u")

        st = client.put(f"/student/{sid}/status", headers=admin_h, json={"status": 0}).json()
        try_check("status update", st.get("code") == 0 and st["data"]["status"] == 0)
        client.put(f"/student/{sid}/status", headers=admin_h, json={"status": 1})

        lst = client.get("/student/list", headers=admin_h, params={"name": marker, "pageSize": 50}).json()
        try_check("admin list filter", lst.get("code") == 0 and any(x["id"] == sid for x in lst["data"]["list"]))

        # teacher write denied
        tw = client.post(
            "/student",
            headers=teacher_h,
            json={"name": "x", "studentNo": f"TX{suffix}"},
        )
        try_check("teacher create denied", tw.status_code == 403 or tw.json().get("code") == 403)

        # teacher no profile
        ol = client.get("/student/list", headers=orphan_h).json()
        try_check("orphan teacher list 403", ol.get("code") == 403)

        # teacher with profile but no enrollments → empty list
        empty = client.get("/student/list", headers=teacher_h, params={"name": marker}).json()
        try_check(
            "teacher no enrollment empty",
            empty.get("code") == 0 and empty["data"]["list"] == [],
            str(empty.get("message")),
        )

        # ---- enrollment ----
        db = SessionLocal()
        try:
            # 找 teacher 名下任意课程
            course = db.scalar(select(Course).where(Course.teacher_id == int(teacher_id)).limit(1))
            other = db.scalar(select(Course).where(Course.teacher_id != int(teacher_id)).limit(1))
            try_check("teacher owned course exists", course is not None)
            course_id = course.id
            other_id = other.id if other else None
        finally:
            db.close()

        enr = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        try_check("admin enroll ok", enr.get("code") == 0, str(enr.get("message")))
        eid = enr["data"]["id"]
        created_enrollment_ids.append(eid)

        enr2 = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        try_check("duplicate enroll rejected", enr2.get("code") == 400)

        # teacher cannot enroll
        te = client.post(
            "/enrollment",
            headers=teacher_h,
            json={"studentId": sid, "courseId": course_id},
        )
        try_check("teacher enroll denied", te.status_code == 403 or te.json().get("code") == 403)

        # missing student/course
        miss_s = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": 99999999, "courseId": course_id},
        ).json()
        try_check("missing student 404", miss_s.get("code") == 404)
        miss_c = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": 99999999},
        ).json()
        try_check("missing course 404", miss_c.get("code") == 404)

        # teacher now sees student
        tlist = client.get("/student/list", headers=teacher_h, params={"name": marker}).json()
        try_check(
            "teacher sees enrolled student",
            tlist.get("code") == 0 and any(x["id"] == sid for x in tlist["data"]["list"]),
        )
        tdet = client.get(f"/student/{sid}", headers=teacher_h).json()
        try_check("teacher detail own student", tdet.get("code") == 0)

        # create another student not enrolled → IDOR
        create2 = client.post(
            "/student",
            headers=admin_h,
            json={"name": marker + "_other", "studentNo": f"T433O{suffix}"},
        ).json()
        try_check("create other student", create2.get("code") == 0)
        sid2 = create2["data"]["id"]
        created_student_ids.append(sid2)
        idor = client.get(f"/student/{sid2}", headers=teacher_h).json()
        try_check("teacher IDOR blocked", idor.get("code") == 403)

        if other_id:
            # enroll into other teacher course — still shouldn't show to this teacher unless also in own
            enr_o = client.post(
                "/enrollment",
                headers=admin_h,
                json={"studentId": sid2, "courseId": other_id},
            ).json()
            if enr_o.get("code") == 0:
                created_enrollment_ids.append(enr_o["data"]["id"])
            hidden = client.get(f"/student/{sid2}", headers=teacher_h).json()
            try_check("other teacher student hidden", hidden.get("code") == 403)

        drop = client.put(f"/enrollment/{eid}/drop", headers=admin_h).json()
        try_check("admin drop ok", drop.get("code") == 0 and drop["data"]["status"] == 0)
        # re-enroll restores
        enr3 = client.post(
            "/enrollment",
            headers=admin_h,
            json={"studentId": sid, "courseId": course_id},
        ).json()
        try_check("re-enroll restores", enr3.get("code") == 0 and enr3["data"]["status"] == 1)
        try_check("re-enroll same id", enr3["data"]["id"] == eid)

        # ---- resources ----
        # admin upload
        files = {
            "file": (
                "hello_测试.pdf",
                io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" * 2),
                "application/pdf",
            ),
        }
        up = client.post(
            "/resource/upload",
            headers=admin_h,
            data={"courseId": str(course_id)},
            files=files,
        ).json()
        try_check("admin upload ok", up.get("code") == 0, str(up.get("message")))
        rid = up["data"]["id"]
        created_resource_ids.append(rid)

        db = SessionLocal()
        try:
            row = db.get(Resource, rid)
            try_check("resource db row", row is not None and row.file_path)
            rel = row.file_path
            abs_path = safe_relative_path(rel)
            try_check("file on disk", abs_path.is_file())
            try_check("file under upload root", str(abs_path).startswith(str(upload_root())))
        finally:
            db.close()

        # teacher list own
        rl = client.get("/resource/list", headers=teacher_h).json()
        try_check("teacher list ok", rl.get("code") == 0)
        try_check(
            "teacher sees own resource",
            any(x["id"] == rid for x in rl["data"]["list"]),
        )

        # teacher upload own course（合法最小 OOXML，满足内容校验）
        docx_buf = io.BytesIO()
        with zipfile.ZipFile(docx_buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types></Types>")
            zf.writestr("word/document.xml", "<w:document/>")
        up_t = client.post(
            "/resource/upload",
            headers=teacher_h,
            data={"courseId": str(course_id)},
            files={
                "file": (
                    "t_note.docx",
                    io.BytesIO(docx_buf.getvalue()),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        ).json()
        try_check("teacher upload own", up_t.get("code") == 0, str(up_t.get("message")))
        if up_t.get("code") == 0:
            created_resource_ids.append(up_t["data"]["id"])

        # teacher unauthorized upload
        if other_id:
            before_files = set(p.name for p in (upload_root() / "courses" / str(other_id)).glob("*")) if (upload_root() / "courses" / str(other_id)).exists() else set()
            bad_up = client.post(
                "/resource/upload",
                headers=teacher_h,
                data={"courseId": str(other_id)},
                files={"file": ("hack.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
            ).json()
            try_check("teacher cross upload denied", bad_up.get("code") == 403)
            after_files = set(p.name for p in (upload_root() / "courses" / str(other_id)).glob("*")) if (upload_root() / "courses" / str(other_id)).exists() else set()
            try_check("no orphan file on denied upload", before_files == after_files)

        # illegal type
        bad_type = client.post(
            "/resource/upload",
            headers=admin_h,
            data={"courseId": str(course_id)},
            files={"file": ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        ).json()
        try_check("illegal type rejected", bad_type.get("code") == 400)

        # download
        dl = client.get(f"/resource/{rid}/download", headers=admin_h)
        try_check("admin download", dl.status_code == 200 and len(dl.content) > 0)
        dl_t = client.get(f"/resource/{rid}/download", headers=teacher_h)
        try_check("teacher download own", dl_t.status_code == 200)

        if other_id:
            # create resource on other course as admin then teacher download denied
            up_o = client.post(
                "/resource/upload",
                headers=admin_h,
                data={"courseId": str(other_id)},
                files={
                    "file": (
                        "other.pdf",
                        io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\nother\n"),
                        "application/pdf",
                    )
                },
            ).json()
            if up_o.get("code") == 0:
                created_resource_ids.append(up_o["data"]["id"])
                dl_bad = client.get(f"/resource/{up_o['data']['id']}/download", headers=teacher_h).json()
                try_check("teacher download other denied", dl_bad.get("code") == 403)

        # course detail resources from MySQL
        detail = client.get(f"/course/{course_id}", headers=admin_h).json()
        try_check("course detail has resources", detail.get("code") == 0)
        try_check(
            "course detail includes uploaded",
            any(r["id"] == rid for r in detail["data"].get("resources", [])),
        )

        # teacher delete denied
        del_t = client.delete(f"/resource/{rid}", headers=teacher_h)
        try_check("teacher delete denied", del_t.status_code == 403 or del_t.json().get("code") == 403)

        # admin delete resource + file
        db = SessionLocal()
        try:
            rel_del = db.get(Resource, rid).file_path
            path_del = safe_relative_path(rel_del)
        finally:
            db.close()
        del_a = client.delete(f"/resource/{rid}", headers=admin_h).json()
        try_check("admin delete resource", del_a.get("code") == 0)
        try_check("file cleaned after delete", not path_del.exists())
        created_resource_ids = [x for x in created_resource_ids if x != rid]

        # null file_path download
        db = SessionLocal()
        try:
            null_row = Resource(
                course_id=course_id,
                name="meta-only.pdf",
                type="PDF",
                size=100,
                uploader="admin",
                uploaded_at=__import__("datetime").datetime.now(),
                status=1,
                file_path=None,
            )
            db.add(null_row)
            db.commit()
            db.refresh(null_row)
            null_id = null_row.id
            created_resource_ids.append(null_id)
        finally:
            db.close()
        dl_null = client.get(f"/resource/{null_id}/download", headers=admin_h).json()
        try_check("null file_path download error", dl_null.get("code") == 404)

        # course delete with enrollment blocked
        del_c = client.delete(f"/course/{course_id}", headers=admin_h).json()
        try_check("course delete blocked by enrollment", del_c.get("code") == 409)

        # create disposable course + resource then delete course cleans file
        db = SessionLocal()
        try:
            cat_id = db.execute(text("SELECT id FROM course_categories LIMIT 1")).scalar()
            new_c = Course(
                name=f"DelCourse_{suffix}",
                category_id=cat_id,
                teacher_id=int(teacher_id),
                cover="",
                duration=1,
                student_count=0,
                learn_count=0,
                completion_rate=0,
                status=1,
                intro="",
                chapters_json=[],
                created_at=__import__("datetime").date.today(),
            )
            db.add(new_c)
            db.commit()
            db.refresh(new_c)
            created_course_ids.append(new_c.id)
            disposable_id = new_c.id
        finally:
            db.close()

        up_d = client.post(
            "/resource/upload",
            headers=admin_h,
            data={"courseId": str(disposable_id)},
            files={
                "file": (
                    "gone.pdf",
                    io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\ngone\n"),
                    "application/pdf",
                )
            },
        ).json()
        try_check("upload on disposable course", up_d.get("code") == 0)
        rid_d = up_d["data"]["id"]
        db = SessionLocal()
        try:
            path_d = safe_relative_path(db.get(Resource, rid_d).file_path)
        finally:
            db.close()
        del_course = client.delete(f"/course/{disposable_id}", headers=admin_h).json()
        try_check("delete course cleans resources", del_course.get("code") == 0)
        try_check("course resource file cleaned", not path_d.exists())
        created_course_ids = [x for x in created_course_ids if x != disposable_id]
        created_resource_ids = [x for x in created_resource_ids if x != rid_d]

        # dashboard studentTotal
        dash = client.get("/dashboard", headers=admin_h).json()
        db = SessionLocal()
        try:
            cnt = int(db.scalar(select(func.count(Student.id))) or 0)
        finally:
            db.close()
        try_check(
            "dashboard studentTotal matches COUNT",
            dash.get("code") == 0 and dash["data"]["cards"]["studentTotal"] == cnt,
            f"api={dash['data']['cards']['studentTotal']} db={cnt}",
        )

        # demo tables unchanged counts (users/teachers/categories; courses may +0 after cleanup)
        db = SessionLocal()
        try:
            try_check("users intact", db.scalar(select(func.count(User.id))) >= base_users)
            try_check("teachers intact", db.scalar(select(func.count(Teacher.id))) >= base_teachers)
            try_check(
                "categories intact",
                db.execute(text("SELECT COUNT(*) FROM course_categories")).scalar() == base_cats,
            )
        finally:
            db.close()

    finally:
        cleanup()

    print(f"\n=== RESULT: {'PASS' if fail_count == 0 else 'FAIL'}  fails={fail_count} ===")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
