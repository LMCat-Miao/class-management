"""
4.3.1.3.1 新增课程 status 合法性校验。

独立测试课；验证 POST /course 仅接受 0/1；未传默认 1；
Service 层防御；非法 bool 拒绝。

用法：

    python scripts\\test_course_create_status_validation.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

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
    from app.services.course_write import CourseWriteError, create_course

    client = TestClient(app)
    marker = f"__TEST_CREATE_STATUS_{uuid.uuid4().hex[:8]}__"
    created_ids: list[int] = []

    def cleanup() -> None:
        if not created_ids:
            return
        db = SessionLocal()
        try:
            for cid in created_ids:
                row = db.get(Course, cid)
                if row:
                    db.delete(row)
            db.commit()
            print(f"[cleanup] deleted test courses {created_ids}")
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[cleanup][FAIL] {exc}")
            raise
        finally:
            db.close()

    def track(body: dict) -> int:
        cid = body["data"]["id"]
        created_ids.append(cid)
        return cid

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}

        base = {
            "name": marker,
            "category": "前端",
            "teacherId": 1,
            "duration": 1,
            "intro": "create-status",
        }

        # status=0
        r = client.post("/course", headers=admin_h, json={**base, "name": marker + "_0", "status": 0})
        body = r.json()
        check("status=0 create 200", r.status_code == 200 and body.get("code") == 0, str(body))
        cid0 = track(body)
        check("status=0 in response", body["data"].get("status") == 0)
        db = SessionLocal()
        try:
            check("status=0 in mysql", db.get(Course, cid0).status == 0)
        finally:
            db.close()

        # status=1
        r = client.post("/course", headers=admin_h, json={**base, "name": marker + "_1", "status": 1})
        body = r.json()
        check("status=1 create 200", r.status_code == 200 and body.get("code") == 0)
        cid1 = track(body)
        check("status=1 in response", body["data"].get("status") == 1)

        # illegal numeric → 400
        for bad in (2, -1, 999):
            r = client.post(
                "/course",
                headers=admin_h,
                json={**base, "name": f"{marker}_bad_{bad}", "status": bad},
            )
            check(f"status={bad} rejected 400", r.status_code == 400, f"status={r.status_code}")
            check(f"status={bad} no data", r.json().get("data") is None)

        # true/false via HTTP：进入 Service 后 400（Schema 保留 bool，避免被收成 0/1）
        for flag in (True, False):
            r = client.post(
                "/course",
                headers=admin_h,
                json={**base, "name": f"{marker}_bool_{flag}", "status": flag},
            )
            check(
                f"HTTP status={flag!r} rejected 400",
                r.status_code == 400,
                f"status={r.status_code} body={r.text[:200]}",
            )
            check(f"HTTP status={flag!r} no data", r.json().get("data") is None)

        # omit status → default 1
        r = client.post("/course", headers=admin_h, json={**base, "name": marker + "_default"})
        body = r.json()
        check("omit status 200", r.status_code == 200 and body.get("code") == 0)
        cid_def = track(body)
        check("omit status defaults to 1", body["data"].get("status") == 1)
        db = SessionLocal()
        try:
            check("omit status mysql 1", db.get(Course, cid_def).status == 1)
        finally:
            db.close()

        # teacher 403
        r = client.post(
            "/course",
            headers=teacher_h,
            json={**base, "name": marker + "_by_teacher", "status": 1},
        )
        check("teacher create 403", r.status_code == 403)

        # no token 401
        r = client.post("/course", json={**base, "name": marker + "_anon"})
        check("no token 401", r.status_code == 401)

        # Service-level defense
        db = SessionLocal()
        try:
            for bad in (2, -1, 999, True, False):
                try:
                    create_course(
                        db,
                        SimpleNamespace(
                            name=f"{marker}_svc_{bad}",
                            category="前端",
                            teacherId=1,
                            duration=1,
                            status=bad,
                            intro="",
                            cover=None,
                            difficulty="初级",
                            chapters=None,
                        ),
                    )
                    check(f"service reject {bad!r}", False)
                except CourseWriteError as exc:
                    check(f"service reject {bad!r}", exc.status_code == 400)

            # Service omit status (attribute missing) → default 1
            created = create_course(
                db,
                SimpleNamespace(
                    name=marker + "_svc_default",
                    category="前端",
                    teacherId=1,
                    duration=1,
                    intro="",
                    cover=None,
                    difficulty="初级",
                    chapters=None,
                ),
            )
            created_ids.append(created["id"])
            check("service omit status -> 1", created.get("status") == 1)
        finally:
            db.close()

        # 成功创建：status=0、status=1、omit 默认、Service omit → 共 4 条
        check("successful creates tracked", len(created_ids) == 4, str(created_ids))

        print("[course-create-status-validation] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
