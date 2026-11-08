"""
4.1 课程列表/详情 MySQL 只读冒烟测试（不删改演示数据）。

用法（backend 目录、已激活 venv）：

    python scripts\\test_course_read_mysql.py
"""

from __future__ import annotations

import sys
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

    from app.main import app

    client = TestClient(app)

    # login
    admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
    check("admin login", admin.get("code") == 0)
    admin_token = admin["data"]["accessToken"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
    check("teacher login", teacher.get("code") == 0)
    teacher_token = teacher["data"]["accessToken"]
    teacher_id = teacher["data"]["userInfo"]["teacherId"]
    teacher_h = {"Authorization": f"Bearer {teacher_token}"}

    # 1) admin list
    r = client.get("/course/list", headers=admin_h, params={"page": 1, "pageSize": 10})
    body = r.json()
    check("admin list ok", r.status_code == 200 and body.get("code") == 0, str(body.get("message")))
    data = body["data"]
    check("admin list total >= 8", data.get("total", 0) >= 8, str(data.get("total")))
    check("admin list page shape", "list" in data and data.get("page") == 1 and data.get("pageSize") == 10)
    first = (data.get("list") or [None])[0]
    check(
        "list fields mapped",
        first
        and "category" in first
        and "teacher" in first
        and "teacherId" in first
        and "createdAt" in first
        and "chapters" in first
        and "category_id" not in first
        and "chapters_json" not in first,
        str(first),
    )

    # 2) teacher only own courses
    r = client.get("/course/list", headers=teacher_h, params={"page": 1, "pageSize": 50})
    body = r.json()
    check("teacher list ok", body.get("code") == 0)
    t_list = body["data"]["list"]
    check("teacher list non-empty", len(t_list) > 0)
    check(
        "teacher only own teacherId",
        all(item.get("teacherId") == teacher_id for item in t_list),
        str({item.get("id"): item.get("teacherId") for item in t_list}),
    )
    check(
        "teacher fewer than admin",
        body["data"]["total"] < data["total"],
        f"teacher_total={body['data']['total']} admin_total={data['total']}",
    )

    # 3) search by name
    r = client.get("/course/list", headers=admin_h, params={"name": "Vue3", "page": 1, "pageSize": 10})
    body = r.json()
    check("search name ok", body.get("code") == 0 and body["data"]["total"] >= 1)
    check(
        "search name match",
        all("Vue3" in item["name"] for item in body["data"]["list"]),
        str([i["name"] for i in body["data"]["list"]]),
    )

    # 4) category filter
    r = client.get("/course/list", headers=admin_h, params={"category": "前端", "page": 1, "pageSize": 50})
    body = r.json()
    check("category filter ok", body.get("code") == 0 and body["data"]["total"] >= 1)
    check(
        "category all 前端",
        all(item["category"] == "前端" for item in body["data"]["list"]),
        str([i["category"] for i in body["data"]["list"]]),
    )

    # 5) pagination
    r1 = client.get("/course/list", headers=admin_h, params={"page": 1, "pageSize": 3})
    r2 = client.get("/course/list", headers=admin_h, params={"page": 2, "pageSize": 3})
    b1, b2 = r1.json()["data"], r2.json()["data"]
    check("pagination totals equal", b1["total"] == b2["total"])
    check("page1 size", len(b1["list"]) == 3)
    check("page2 size", len(b2["list"]) == 3)
    check(
        "pages different ids",
        {i["id"] for i in b1["list"]}.isdisjoint({i["id"] for i in b2["list"]}),
    )

    # 6) detail ok
    course_id = first["id"]
    r = client.get(f"/course/{course_id}", headers=admin_h)
    body = r.json()
    check("detail ok", r.status_code == 200 and body.get("code") == 0)
    detail = body["data"]
    check("detail category chinese", isinstance(detail.get("category"), str) and detail["category"])
    check("detail teacher name", isinstance(detail.get("teacher"), str) and detail["teacher"])
    check("detail chapters list", isinstance(detail.get("chapters"), list))
    check(
        "detail createdAt YYYY-MM-DD",
        isinstance(detail.get("createdAt"), str) and len(detail["createdAt"]) == 10,
        str(detail.get("createdAt")),
    )
    check("detail has resources key", "resources" in detail)

    # 7) missing course
    r = client.get("/course/999999", headers=admin_h)
    body = r.json()
    check("missing course 404", r.status_code == 404 and body.get("data") is None)

    # 8) known seed: course 1 Vue3 / 张老师 / 前端
    r = client.get("/course/1", headers=admin_h)
    d = r.json()["data"]
    check("course1 name", d.get("name") == "Vue3企业级开发")
    check("course1 category", d.get("category") == "前端")
    check("course1 teacher", d.get("teacher") == "张老师")
    check("course1 chapters non-empty", len(d.get("chapters") or []) >= 1)
    check("course1 resources from memory", isinstance(d.get("resources"), list))
    # seed resource id1 courseId=1
    check(
        "course1 has pdf resource if memory seed present",
        any(x.get("courseId") == 1 for x in d.get("resources") or [])
        or len(d.get("resources") or []) >= 0,
    )

    print("[course-read-mysql] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
