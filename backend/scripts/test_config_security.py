"""
配置安全专项测试（不访问 MySQL，不修改真实 .env）。

验证 APP_ENV + SECRET_KEY 在开发 / 生产下的校验规则。

用法（backend 目录、venv）：

    python scripts\\test_config_security.py
"""

from __future__ import annotations

import sys
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
    from app.core.config import (
        DEV_SECRET_KEY,
        ConfigSecurityError,
        Settings,
        validate_settings,
    )

    # 1) 开发环境 + 默认 Secret：允许
    dev = Settings(
        _env_file=None,
        app_env="development",
        secret_key=DEV_SECRET_KEY,
    )
    try:
        validate_settings(dev)
        check("dev default secret allowed", True)
    except ConfigSecurityError as exc:
        check("dev default secret allowed", False, str(exc))

    # 2) 生产环境未设置 / 空 Secret：失败
    prod_empty = Settings(
        _env_file=None,
        app_env="production",
        secret_key="   ",
    )
    try:
        validate_settings(prod_empty)
        check("prod empty secret rejected", False)
    except ConfigSecurityError as exc:
        msg = str(exc)
        check("prod empty secret rejected", True)
        check("empty-error has no secret plaintext", DEV_SECRET_KEY not in msg and "   " not in msg.strip())

    # 3) 生产环境使用开发默认 Secret：失败
    prod_devkey = Settings(
        _env_file=None,
        app_env="production",
        secret_key=DEV_SECRET_KEY,
    )
    try:
        validate_settings(prod_devkey)
        check("prod default secret rejected", False)
    except ConfigSecurityError as exc:
        msg = str(exc)
        check("prod default secret rejected", True)
        check("reject-error has no secret plaintext", DEV_SECRET_KEY not in msg)

    # prod 别名
    prod_alias = Settings(
        _env_file=None,
        app_env="PROD",
        secret_key=DEV_SECRET_KEY,
    )
    try:
        validate_settings(prod_alias)
        check("APP_ENV=prod alias rejected default", False)
    except ConfigSecurityError:
        check("APP_ENV=prod alias rejected default", True)

    # 4) 生产环境合法强随机 Secret：通过
    strong = "unit-test-only-strong-secret-key-not-for-deploy-9f3a"
    prod_ok = Settings(
        _env_file=None,
        app_env="production",
        secret_key=strong,
    )
    try:
        validate_settings(prod_ok)
        check("prod strong secret accepted", True)
    except ConfigSecurityError as exc:
        check("prod strong secret accepted", False, str(exc))

    # 5) 再次确认错误文案不含明文密钥
    try:
        validate_settings(
            Settings(_env_file=None, app_env="production", secret_key=DEV_SECRET_KEY)
        )
    except ConfigSecurityError as exc:
        blob = str(exc)
        check("final: message omits DEV_SECRET_KEY", DEV_SECRET_KEY not in blob)
        check("final: message mentions production", "生产" in blob or "production" in blob.lower())

    print("[config-security] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
