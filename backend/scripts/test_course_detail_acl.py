"""
课程详情教师归属权限冒烟测试。

用法（backend 目录）：

    python scripts\\test_course_detail_acl.py
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

    admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
    check("admin login", admin.get("code") == 0)
    admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

    teacher = client.post("/login", json={"username": "teacher", "password": "123456"}).json()
    check("teacher login", teacher.get("code") == 0)
    teacher_h = {"Authorization": f"Bearer {teacher['data']['accessToken']}"}
    check("teacher teacherId == 1 (Zhang)", teacher["data"]["userInfo"].get("teacherId") == 1)

    # Seed: course 1 -> 张老师(id=1); course 2 -> 李老师(id=2)
    # 1) admin -> Zhang's course
    r = client.get("/course/1", headers=admin_h)
    check("admin read Zhang course 200", r.status_code == 200 and r.json().get("code") == 0)

    # 2) admin -> other teacher course
    r = client.get("/course/2", headers=admin_h)
    check("admin read Li course 200", r.status_code == 200 and r.json().get("code") == 0)

    # 3) teacher -> own course
    r = client.get("/course/1", headers=teacher_h)
    body = r.json()
    check("teacher read own course 200", r.status_code == 200 and body.get("code") == 0)
    check("own course teacherId 1", body["data"].get("teacherId") == 1)

    # 4) teacher -> others' course
    r = client.get("/course/2", headers=teacher_h)
    body = r.json()
    check("teacher read others 403", r.status_code == 403, f"status={r.status_code}")
    check(
        "403 body shape",
        body.get("code") == 403 and body.get("data") is None and bool(body.get("message")),
        str(body),
    )

    # 5) missing course
    r = client.get("/course/999999", headers=admin_h)
    check("missing 404", r.status_code == 404 and r.json().get("data") is None)

    # teacher missing still 404 (not 403)
    r = client.get("/course/999999", headers=teacher_h)
    check("teacher missing 404", r.status_code == 404)

    # 6) no token
    r = client.get("/course/1")
    check("no token 401", r.status_code == 401)

    print("[course-detail-acl] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
