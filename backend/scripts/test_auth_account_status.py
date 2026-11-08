"""
4.4.2 认证与教师账号状态专项测试。

使用独立临时用户/教师档案；try/finally 清理。
不修改演示 admin/teacher 账号密码，不停用演示教师。

用法：

    python scripts\\test_auth_account_status.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
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
    from jose import jwt
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.core.security import hash_password
    from app.db.database import SessionLocal
    from app.main import app
    from app.models.teacher import Teacher
    from app.models.user import User

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    orphan_uid: int | None = None
    active_uid: int | None = None
    active_tid: int | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            if active_tid is not None:
                t = db.get(Teacher, active_tid)
                if t:
                    db.delete(t)
                    db.commit()
            for uid in (orphan_uid, active_uid):
                if uid is None:
                    continue
                u = db.get(User, uid)
                if u:
                    db.delete(u)
                    db.commit()
            print("[cleanup] temp auth fixtures removed")
        except Exception as exc:
            db.rollback()
            print(f"[cleanup][WARN] {exc}")
        finally:
            db.close()

    try:
        # --- demo accounts unchanged ---
        r = client.post("/login", json={"username": "admin", "password": "123456"})
        body = r.json()
        check("admin login", r.status_code == 200 and body.get("code") == 0)
        check("admin has accessToken", bool(body["data"].get("accessToken")))
        check("admin no refreshToken", "refreshToken" not in (body.get("data") or {}))
        admin_h = {"Authorization": f"Bearer {body['data']['accessToken']}"}

        r = client.post("/login", json={"username": "teacher", "password": "123456"})
        body = r.json()
        check("demo teacher login", r.status_code == 200 and body.get("code") == 0)
        check("demo teacher no refreshToken", "refreshToken" not in (body.get("data") or {}))
        teacher_h = {"Authorization": f"Bearer {body['data']['accessToken']}"}
        demo_tid = body["data"]["userInfo"]["teacherId"]

        r = client.post("/login", json={"username": "admin", "password": "wrong"})
        check("bad password 401", r.status_code == 401)

        r = client.get("/user/info", headers=admin_h)
        check("admin token /user/info", r.status_code == 200 and r.json().get("code") == 0)

        r = client.get("/dashboard", headers=teacher_h)
        check("teacher token dashboard", r.status_code == 200 and r.json().get("code") == 0)

        r = client.get("/user/info")
        check("no token 401", r.status_code == 401)

        r = client.get("/user/info", headers={"Authorization": "Bearer not-a-jwt"})
        check("invalid token 401", r.status_code == 401)

        # expired token
        expired = jwt.encode(
            {
                "sub": "1",
                "role": "admin",
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            },
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        r = client.get("/user/info", headers={"Authorization": f"Bearer {expired}"})
        check("expired token 401", r.status_code == 401)

        # nonexistent user id token
        missing = jwt.encode(
            {
                "sub": "99999999",
                "role": "admin",
                "type": "access",
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            },
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        r = client.get("/user/info", headers={"Authorization": f"Bearer {missing}"})
        check("missing user token 401", r.status_code == 401)

        # orphan teacher user (no teachers row)
        db = SessionLocal()
        try:
            ou = User(
                username=f"tmp_auth_orphan_{suffix}",
                nickname="orphan",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(ou)
            db.commit()
            db.refresh(ou)
            orphan_uid = ou.id

            au = User(
                username=f"tmp_auth_active_{suffix}",
                nickname="active-t",
                password_hash=hash_password("123456"),
                role="teacher",
            )
            db.add(au)
            db.flush()
            at = Teacher(
                user_id=au.id,
                name=f"临时认证教师_{suffix}",
                avatar="",
                phone="",
                email="",
                title="讲师",
                status=1,
            )
            db.add(at)
            db.commit()
            db.refresh(au)
            db.refresh(at)
            active_uid = au.id
            active_tid = at.id
        finally:
            db.close()

        r = client.post(
            "/login",
            json={"username": f"tmp_auth_orphan_{suffix}", "password": "123456"},
        )
        check("orphan teacher login rejected", r.status_code == 401)
        check(
            "orphan login unified message",
            r.json().get("message") == "用户名或密码错误",
        )

        r = client.post(
            "/login",
            json={"username": f"tmp_auth_active_{suffix}", "password": "123456"},
        )
        body = r.json()
        check("active teacher login", r.status_code == 200 and body.get("code") == 0)
        active_token = body["data"]["accessToken"]
        active_h = {"Authorization": f"Bearer {active_token}"}
        r = client.get("/user/info", headers=active_h)
        check("active teacher /user/info", r.status_code == 200)

        # disable teacher → old token rejected with 403
        db = SessionLocal()
        try:
            t = db.get(Teacher, active_tid)
            t.status = 0
            db.add(t)
            db.commit()
        finally:
            db.close()

        r = client.post(
            "/login",
            json={"username": f"tmp_auth_active_{suffix}", "password": "123456"},
        )
        check("disabled teacher login rejected", r.status_code == 401)

        r = client.get("/user/info", headers=active_h)
        check("disabled teacher old token 403", r.status_code == 403, str(r.json()))
        check(
            "disabled error ACCOUNT_DISABLED",
            r.json().get("error") == "ACCOUNT_DISABLED",
            str(r.json()),
        )
        check("disabled body.code 403", r.json().get("code") == 403)
        r = client.get("/dashboard", headers=active_h)
        check("disabled teacher dashboard 403", r.status_code == 403)

        # re-enable → can login again
        db = SessionLocal()
        try:
            t = db.get(Teacher, active_tid)
            t.status = 1
            db.add(t)
            db.commit()
        finally:
            db.close()

        r = client.post(
            "/login",
            json={"username": f"tmp_auth_active_{suffix}", "password": "123456"},
        )
        check("re-enabled teacher login", r.status_code == 200 and r.json().get("code") == 0)
        new_h = {"Authorization": f"Bearer {r.json()['data']['accessToken']}"}
        r = client.get("/user/info", headers=new_h)
        check("re-enabled teacher /user/info", r.status_code == 200)

        # logout client-session semantics
        r = client.post("/logout", headers=admin_h)
        check("logout ok", r.status_code == 200 and r.json().get("code") == 0)
        # token still cryptographically valid until expiry (no blacklist)
        r = client.get("/user/info", headers=admin_h)
        check("logout does not revoke token server-side", r.status_code == 200)

        # demo teacher still enabled
        db = SessionLocal()
        try:
            demo = db.get(Teacher, demo_tid)
            check("demo teacher still status=1", demo is not None and int(demo.status) == 1)
        finally:
            db.close()

        print("[auth-account-status] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
