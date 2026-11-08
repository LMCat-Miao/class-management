"""
第三阶段：登录认证 MySQL 迁移冒烟测试（只读业务库，不删改 Seed）。

用法（backend 目录、已激活 venv）：

    python scripts\\test_auth_mysql.py
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
    status = "PASS" if cond else "FAIL"
    print(f"{status}  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def main() -> int:
    from fastapi.testclient import TestClient

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.teacher import Teacher

    client = TestClient(app)

    # 1) admin login
    r = client.post("/login", json={"username": "admin", "password": "123456"})
    body = r.json()
    check("admin login ok", r.status_code == 200 and body.get("code") == 0, str(body))
    data = body["data"]
    admin_token = data.get("accessToken")
    check("admin accessToken present", bool(admin_token))
    check("admin no refreshToken", "refreshToken" not in data)
    admin_info = data.get("userInfo") or {}
    check("admin without teacherId", "teacherId" not in admin_info, str(admin_info))
    check(
        "admin roles/permissions",
        admin_info.get("roles") == ["admin"]
        and "course:add" in (admin_info.get("permissions") or []),
    )

    # 2) teacher login
    r = client.post("/login", json={"username": "teacher", "password": "123456"})
    body = r.json()
    check("teacher login ok", r.status_code == 200 and body.get("code") == 0)
    data = body["data"]
    teacher_token = data.get("accessToken")
    tinfo = data.get("userInfo") or {}
    check("teacher has teacherId int", isinstance(tinfo.get("teacherId"), int), str(tinfo))
    teacher_id = tinfo["teacherId"]

    # 3) bad password
    r = client.post("/login", json={"username": "admin", "password": "wrong"})
    check("bad password rejected", r.status_code == 401)

    # 4) missing user
    r = client.post("/login", json={"username": "no_such_user", "password": "123456"})
    check("missing user rejected", r.status_code == 401)

    # 5) admin /user/info
    r = client.get("/user/info", headers={"Authorization": f"Bearer {admin_token}"})
    body = r.json()
    check(
        "admin /user/info ok",
        r.status_code == 200
        and body.get("code") == 0
        and body["data"].get("username") == "admin",
    )

    # 6) teacher /user/info
    r = client.get("/user/info", headers={"Authorization": f"Bearer {teacher_token}"})
    body = r.json()
    check("teacher /user/info ok", r.status_code == 200 and body.get("code") == 0)
    check(
        "teacherId stable on /user/info",
        body["data"].get("teacherId") == teacher_id,
        str(body.get("data")),
    )

    # 7) no token
    r = client.get("/user/info")
    check("no token rejected", r.status_code == 401)

    # 8) invalid token
    r = client.get("/user/info", headers={"Authorization": "Bearer not-a-jwt"})
    check("invalid token rejected", r.status_code == 401)

    # teacherId -> 张老师
    db = SessionLocal()
    try:
        teacher = db.get(Teacher, teacher_id)
        check(
            "teacherId maps to Zhang",
            teacher is not None and teacher.name == "张老师",
            f"id={teacher_id} name={getattr(teacher, 'name', None)}",
        )
    finally:
        db.close()

    print("[auth-mysql] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
