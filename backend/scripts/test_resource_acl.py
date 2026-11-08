"""
资源列表/上传/下载/删除课程归属 ACL（4.3.3 MySQL + 文件）。

专用测试用户、教师档案、课程与资源；finally 清理，不碰演示数据。

用法：

    python scripts\\test_resource_acl.py
"""

from __future__ import annotations

import io
import sys
import uuid
from datetime import datetime
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
    from sqlalchemy import func, select

    from app.core.security import create_access_token, hash_password
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.resource import Resource
    from app.models.teacher import Teacher
    from app.models.user import User
    from app.services.resource_write import safe_relative_path, upload_root

    client = TestClient(app)
    marker = f"__TEST_RES_ACL_{uuid.uuid4().hex[:8]}__"
    suffix = uuid.uuid4().hex[:8]

    course_a_id: int | None = None
    course_b_id: int | None = None
    teacher_b_id: int | None = None
    user_b_id: int | None = None
    orphan_user_id: int | None = None
    test_resource_ids: list[int] = []
    demo_resource_count_start: int | None = None

    def track_resource(rid: int) -> None:
        if rid not in test_resource_ids:
            test_resource_ids.append(rid)

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in list(test_resource_ids):
                row = db.get(Resource, rid)
                if not row:
                    continue
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

            for cid in (course_a_id, course_b_id):
                if cid is None:
                    continue
                # leftover resources on disposable courses
                for row in db.scalars(select(Resource).where(Resource.course_id == cid)).all():
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
                row = db.get(Course, cid)
                if row:
                    db.delete(row)
            db.commit()

            if teacher_b_id is not None:
                t = db.get(Teacher, teacher_b_id)
                if t:
                    db.delete(t)
            if user_b_id is not None:
                u = db.get(User, user_b_id)
                if u:
                    db.delete(u)
            if orphan_user_id is not None:
                u = db.get(User, orphan_user_id)
                if u:
                    db.delete(u)
            db.commit()

            if demo_resource_count_start is not None:
                # demo rows have file_path NULL and fixed names; count of NULL-path resources
                null_cnt = int(
                    db.scalar(
                        select(func.count(Resource.id)).where(Resource.file_path.is_(None))
                    )
                    or 0
                )
                if null_cnt < 4:
                    print(f"[cleanup][WARN] demo-like null file_path resources={null_cnt}")
            print("[cleanup] mysql test fixtures removed")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL] {exc}")
            raise
        finally:
            db.close()

    try:
        db = SessionLocal()
        try:
            demo_resource_count_start = int(db.scalar(select(func.count(Resource.id))) or 0)
        finally:
            db.close()

        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher_a = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher A login", teacher_a.get("code") == 0)
        teacher_a_h = {"Authorization": f"Bearer {teacher_a['data']['accessToken']}"}
        tinfo = client.get("/user/info", headers=teacher_a_h).json()
        teacher_a_id = (tinfo.get("data") or {}).get("teacherId")
        check("teacher A has teacherId", isinstance(teacher_a_id, int), str(teacher_a_id))

        db = SessionLocal()
        try:
            ub = User(
                username=f"tmp_tb_{suffix}",
                nickname=f"临时教师B_{suffix}",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(ub)
            db.flush()
            user_b_id = ub.id
            tb = Teacher(
                user_id=ub.id,
                name=f"临时教师B_{suffix}",
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
                username=f"tmp_orphan_{suffix}",
                nickname=f"无档案教师_{suffix}",
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
            "/login", json={"username": f"tmp_tb_{suffix}", "password": "123456"}
        ).json()
        check("teacher B login", teacher_b.get("code") == 0)
        teacher_b_h = {"Authorization": f"Bearer {teacher_b['data']['accessToken']}"}
        binfo = client.get("/user/info", headers=teacher_b_h).json()
        check(
            "teacher B teacherId",
            (binfo.get("data") or {}).get("teacherId") == teacher_b_id,
        )

        orphan_login = client.post(
            "/login", json={"username": f"tmp_orphan_{suffix}", "password": "123456"}
        )
        check("orphan teacher login rejected", orphan_login.status_code == 401)
        orphan_h = {
            "Authorization": f"Bearer {create_access_token(orphan_user_id, 'teacher')}"
        }
        oinfo = client.get("/user/info", headers=orphan_h).json()
        check("orphan /user/info 403", oinfo.get("code") == 403)

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

        # seed MySQL metadata-only resources (file_path NULL) for list ACL
        db = SessionLocal()
        try:
            ra = Resource(
                course_id=course_a_id,
                name=f"{marker}_A.pdf",
                type="PDF",
                size=1024,
                uploader="tester",
                uploaded_at=datetime(2026, 1, 1, 0, 0),
                status=1,
                file_path=None,
            )
            rb = Resource(
                course_id=course_b_id,
                name=f"{marker}_B.pdf",
                type="PDF",
                size=1024,
                uploader="tester",
                uploaded_at=datetime(2026, 1, 1, 0, 0),
                status=1,
                file_path=None,
            )
            db.add(ra)
            db.add(rb)
            db.commit()
            db.refresh(ra)
            db.refresh(rb)
            res_a_id, res_b_id = ra.id, rb.id
            track_resource(res_a_id)
            track_resource(res_b_id)
        finally:
            db.close()

        # ========== A: GET /resource/list ==========
        r = client.get("/resource/list", headers=admin_h, params={"page": 1, "pageSize": 200})
        body = r.json()
        check("A1 admin all 200", r.status_code == 200 and body.get("code") == 0)
        ids = {x["id"] for x in body["data"]["list"]}
        check("A1 admin sees A and B resources", res_a_id in ids and res_b_id in ids)

        r = client.get(
            "/resource/list",
            headers=admin_h,
            params={"courseId": course_a_id, "page": 1, "pageSize": 50},
        )
        body = r.json()
        check("A2 admin by courseId 200", r.status_code == 200 and body.get("code") == 0)
        check(
            "A2 only course A",
            all(x.get("courseId") == course_a_id for x in body["data"]["list"])
            and any(x["id"] == res_a_id for x in body["data"]["list"]),
        )

        r = client.get(
            "/resource/list",
            headers=admin_h,
            params={"courseId": 999999, "page": 1, "pageSize": 10},
        )
        check("A3 admin missing course 404", r.status_code == 404)

        r = client.get(
            "/resource/list",
            headers=teacher_a_h,
            params={"courseId": course_a_id, "page": 1, "pageSize": 50},
        )
        body = r.json()
        check("A4 teacher own course 200", r.status_code == 200 and body.get("code") == 0)
        check("A4 sees own resource", any(x["id"] == res_a_id for x in body["data"]["list"]))

        r = client.get(
            "/resource/list",
            headers=teacher_a_h,
            params={"courseId": course_b_id, "page": 1, "pageSize": 50},
        )
        check("A5 teacher other course 403", r.status_code == 403)

        r = client.get("/resource/list", headers=teacher_a_h, params={"page": 1, "pageSize": 200})
        body = r.json()
        check("A6 teacher no courseId 200", r.status_code == 200 and body.get("code") == 0)
        t_ids = {x["id"] for x in body["data"]["list"]}
        check("A6 has own resource", res_a_id in t_ids)
        check("A6 no other teacher resource", res_b_id not in t_ids)

        r = client.get("/resource/list", headers=orphan_h, params={"page": 1, "pageSize": 10})
        check("A7 orphan teacher 403", r.status_code == 403)

        r = client.get("/resource/list")
        check("A8 no token 401", r.status_code == 401)

        r = client.get("/resource/list", headers={"Authorization": "Bearer not-a-jwt"})
        check("A9 invalid token 401", r.status_code == 401)

        # ========== B: POST /resource/upload ==========
        def upload(headers, course_id: int, filename: str = "t.pdf"):
            return client.post(
                "/resource/upload",
                headers=headers,
                files={
                    "file": (
                        filename,
                        io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"),
                        "application/pdf",
                    )
                },
                data={"courseId": str(course_id)},
            )

        def course_dir_files(cid: int) -> set[str]:
            d = upload_root() / "courses" / str(cid)
            if not d.exists():
                return set()
            return {p.name for p in d.iterdir() if p.is_file()}

        before_b = course_dir_files(course_b_id)
        r = upload(admin_h, course_b_id, f"{marker}_admin.pdf")
        body = r.json()
        check("B1 admin upload any course 200", r.status_code == 200 and body.get("code") == 0)
        check("B1 courseName from MySQL", body["data"].get("courseName") == f"{marker}_B")
        track_resource(body["data"]["id"])
        after_b = course_dir_files(course_b_id)
        check("B1 file created", len(after_b - before_b) >= 1)

        r = upload(teacher_a_h, course_a_id, f"{marker}_ta.pdf")
        body = r.json()
        check("B2 teacher upload own 200", r.status_code == 200 and body.get("code") == 0)
        track_resource(body["data"]["id"])

        before_deny = course_dir_files(course_b_id)
        r = upload(teacher_a_h, course_b_id, f"{marker}_deny.pdf")
        check("B3 teacher upload other 403", r.status_code == 403)
        check("B3 no new file on deny", course_dir_files(course_b_id) == before_deny)

        r = upload(teacher_a_h, 999999, f"{marker}_miss.pdf")
        check("B4 teacher missing course 404", r.status_code == 404)

        r = upload(admin_h, 999999, f"{marker}_admin_miss.pdf")
        check("B5 admin missing course 404", r.status_code == 404)

        r = upload(orphan_h, course_a_id, f"{marker}_orphan.pdf")
        check("B6 orphan upload 403", r.status_code == 403)

        r = client.post(
            "/resource/upload",
            files={"file": ("x.pdf", io.BytesIO(b"x"), "application/pdf")},
            data={"courseId": str(course_a_id)},
        )
        check("B7 no token 401", r.status_code == 401)

        r = client.post(
            "/resource/upload",
            headers={"Authorization": "Bearer not-a-jwt"},
            files={"file": ("x.pdf", io.BytesIO(b"x"), "application/pdf")},
            data={"courseId": str(course_a_id)},
        )
        check("B8 invalid token 401", r.status_code == 401)

        # ========== C: download / delete ACL ==========
        # upload one with file for download tests
        r = upload(admin_h, course_a_id, f"{marker}_dl.pdf")
        check("C0 upload for download", r.json().get("code") == 0)
        dl_id = r.json()["data"]["id"]
        track_resource(dl_id)

        r = client.get(f"/resource/{dl_id}/download", headers=admin_h)
        check("C1 admin download 200", r.status_code == 200)

        r = client.get(f"/resource/{dl_id}/download", headers=teacher_a_h)
        check("C2 teacher download own 200", r.status_code == 200)

        # resource on B
        r = upload(admin_h, course_b_id, f"{marker}_bdl.pdf")
        check("C3 upload B for download", r.json().get("code") == 0)
        b_dl_id = r.json()["data"]["id"]
        track_resource(b_dl_id)

        r = client.get(f"/resource/{b_dl_id}/download", headers=teacher_a_h)
        check("C4 teacher download other 403", r.status_code == 403 or r.json().get("code") == 403)

        r = client.delete(f"/resource/{dl_id}", headers=teacher_a_h)
        check("C5 teacher delete 403", r.status_code == 403)

        r = client.delete(f"/resource/{dl_id}", headers=admin_h)
        check("C6 admin delete 200", r.status_code == 200 and r.json().get("code") == 0)
        test_resource_ids = [x for x in test_resource_ids if x != dl_id]

        # isolation
        r = client.get(
            "/resource/list",
            headers=teacher_a_h,
            params={"courseId": course_b_id},
        )
        check("C teacher A cannot list B by courseId", r.status_code == 403)
        r = upload(teacher_a_h, course_b_id)
        check("C teacher A cannot upload to B", r.status_code == 403)
        r = client.get(
            "/resource/list",
            headers=teacher_b_h,
            params={"courseId": course_a_id},
        )
        check("C teacher B cannot list A", r.status_code == 403)

        print("[resource-acl] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
