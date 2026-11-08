"""
4.2.1 课程新增 MySQL 冒烟测试。

- 使用独立测试课程名，结束后按 ID 从 MySQL 删除（DELETE API 仍走内存，不能靠它清理）。
- 不删改 Seed 演示课。

用法：

    python scripts\\test_course_create_mysql.py
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
    marker = f"__TEST_CREATE_MYSQL_{uuid.uuid4().hex[:8]}__"

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
        check("teacher login", teacher.get("code") == 0)
        teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}

        payload = {
            "name": marker,
            "cover": "",
            "category": "前端",
            "teacherId": 1,
            "difficulty": "中级",
            "duration": 12,
            "status": 1,
            "intro": "4.2.1 smoke test",
        }

        # 1) admin create
        r = client.post("/course", headers=admin_h, json=payload)
        body = r.json()
        check("admin create 200", r.status_code == 200 and body.get("code") == 0, str(body))
        data = body["data"]
        created_id = data.get("id")
        check("auto id assigned", isinstance(created_id, int) and created_id > 0, str(created_id))
        check("category chinese", data.get("category") == "前端")
        check("teacher name", data.get("teacher") == "张老师")
        check("teacherId", data.get("teacherId") == 1)
        check("chapters list", isinstance(data.get("chapters"), list) and len(data["chapters"]) >= 1)
        check(
            "createdAt format",
            isinstance(data.get("createdAt"), str) and len(data["createdAt"]) == 10,
            str(data.get("createdAt")),
        )
        check("no chapters_json leak", "chapters_json" not in data and "category_id" not in data)

        # 3) list sees it
        r = client.get("/course/list", headers=admin_h, params={"name": marker, "page": 1, "pageSize": 10})
        body = r.json()
        check("list finds new course", body.get("code") == 0 and body["data"]["total"] >= 1)
        check(
            "list contains id",
            any(i.get("id") == created_id for i in body["data"]["list"]),
        )

        # 4) detail
        r = client.get(f"/course/{created_id}", headers=admin_h)
        body = r.json()
        check("detail ok", r.status_code == 200 and body.get("code") == 0)
        check("detail name", body["data"].get("name") == marker)

        # 9) bad teacherId
        bad = {**payload, "name": marker + "_bad_teacher", "teacherId": 999999}
        r = client.post("/course", headers=admin_h, json=bad)
        check("bad teacherId rejected", r.status_code == 400, f"status={r.status_code} body={r.json()}")

        # 10) bad category
        bad = {**payload, "name": marker + "_bad_cat", "category": "不存在的分类XYZ"}
        r = client.post("/course", headers=admin_h, json=bad)
        check("bad category rejected", r.status_code == 400, f"status={r.status_code}")

        # missing teacherId
        bad = {**payload, "name": marker + "_no_teacher"}
        bad.pop("teacherId", None)
        r = client.post("/course", headers=admin_h, json=bad)
        check("missing teacherId rejected", r.status_code == 400)

        # 11) teacher 403
        r = client.post("/course", headers=teacher_h, json={**payload, "name": marker + "_by_teacher"})
        check("teacher create 403", r.status_code == 403)

        # 12) no token 401
        r = client.post("/course", json={**payload, "name": marker + "_anon"})
        check("no token 401", r.status_code == 401)

        print("[course-create-mysql] checks passed")
        return 0
    finally:
        cleanup_course(created_id)


if __name__ == "__main__":
    raise SystemExit(main())
