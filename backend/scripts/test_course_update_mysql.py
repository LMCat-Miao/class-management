"""
4.2.2 课程编辑 MySQL 冒烟测试。

先创建专用测试课，再测部分更新 / 校验 / 权限；finally 中从 MySQL 删除。

用法：

    python scripts\\test_course_update_mysql.py
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

    from app.main import app

    client = TestClient(app)
    created_id: int | None = None
    marker = f"__TEST_UPDATE_MYSQL_{uuid.uuid4().hex[:8]}__"

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}

        # seed dedicated course via POST (already MySQL)
        create_body = {
            "name": marker,
            "category": "前端",
            "teacherId": 1,
            "difficulty": "中级",
            "duration": 10,
            "status": 1,
            "intro": "before-update",
            "chapters": [
                {"id": 1, "title": "第一章 原始"},
                {"id": 2, "title": "第二章 原始"},
            ],
        }
        r = client.post("/course", headers=admin_h, json=create_body)
        body = r.json()
        check("create fixture", r.status_code == 200 and body.get("code") == 0, str(body))
        created_id = body["data"]["id"]
        before = body["data"]

        # 1) full-ish edit success
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={
                "name": marker + "_edited",
                "category": "AI",
                "teacherId": 2,
                "difficulty": "高级",
                "duration": 20,
                "status": 0,
                "intro": "after-update",
            },
        )
        body = r.json()
        check("admin update 200", r.status_code == 200 and body.get("code") == 0, str(body))
        data = body["data"]
        check("name updated", data.get("name") == marker + "_edited")
        check("category chinese AI", data.get("category") == "AI")
        check("teacher Li", data.get("teacher") == "李老师" and data.get("teacherId") == 2)

        # 2) re-fetch from MySQL via GET detail
        r = client.get(f"/course/{created_id}", headers=admin_h)
        detail = r.json()["data"]
        check("detail persisted name", detail.get("name") == marker + "_edited")
        check("detail persisted category", detail.get("category") == "AI")
        check("detail persisted intro", detail.get("intro") == "after-update")

        # 3) partial update: only name
        snap_teacher = detail.get("teacherId")
        snap_cat = detail.get("category")
        snap_intro = detail.get("intro")
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_only_name"},
        )
        body = r.json()
        check("partial name 200", body.get("code") == 0)
        data = body["data"]
        check("only name changed", data.get("name") == marker + "_only_name")
        check("teacher unchanged", data.get("teacherId") == snap_teacher)
        check("category unchanged", data.get("category") == snap_cat)
        check("intro unchanged", data.get("intro") == snap_intro)

        # 4) omit chapters → keep original chapters from create (still 原始 titles
        #    unless overwritten — after edits we never sent chapters, so still create chapters)
        r = client.get(f"/course/{created_id}", headers=admin_h)
        chapters = r.json()["data"].get("chapters") or []
        check(
            "chapters preserved when omitted",
            any(c.get("title") == "第一章 原始" for c in chapters),
            str(chapters),
        )

        # 5) explicit chapters update
        new_chapters = [{"id": 1, "title": "第一章 已改"}]
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_only_name", "chapters": new_chapters},
        )
        check("chapters update 200", r.json().get("code") == 0)
        chapters = r.json()["data"].get("chapters") or []
        check(
            "chapters replaced",
            len(chapters) == 1 and chapters[0].get("title") == "第一章 已改",
            str(chapters),
        )

        # 6) duration=0
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_only_name", "duration": 0},
        )
        check("duration 0 saved", r.json().get("code") == 0 and r.json()["data"].get("duration") == 0)
        r = client.get(f"/course/{created_id}", headers=admin_h)
        check("duration 0 persisted", r.json()["data"].get("duration") == 0)

        # 7) bad category
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_only_name", "category": "不存在分类ABC"},
        )
        check("bad category 400", r.status_code == 400)

        # 8) bad teacherId
        r = client.put(
            f"/course/{created_id}",
            headers=admin_h,
            json={"name": marker + "_only_name", "teacherId": 999999},
        )
        check("bad teacherId 400", r.status_code == 400)

        # 9) missing course
        r = client.put(
            "/course/999999",
            headers=admin_h,
            json={"name": "ghost"},
        )
        check("missing course 404", r.status_code == 404)

        # 10) teacher 403
        r = client.put(
            f"/course/{created_id}",
            headers=teacher_h,
            json={"name": "hack"},
        )
        check("teacher update 403", r.status_code == 403)

        # 11) no token 401
        r = client.put(f"/course/{created_id}", json={"name": "anon"})
        check("no token 401", r.status_code == 401)

        # silence unused before var lint
        _ = before

        print("[course-update-mysql] all checks passed")
        return 0
    finally:
        cleanup_course(created_id)


if __name__ == "__main__":
    raise SystemExit(main())
