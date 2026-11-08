"""
数据库连接测试脚本（第一阶段）。

在 Windows CMD 中（已激活 venv，且位于 backend 目录）：

    python scripts\\test_db_connection.py

预期成功输出：
    [OK] 配置读取成功: host=... db=class_management
    [OK] Engine 连接成功 (SELECT 1)
    [OK] 核心表检查: users, teachers, course_categories, courses 均存在

若尚未执行迁移，表检查会提示缺失，但连接成功仍说明账号/库名配置正确。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 保证以脚本方式运行时也能 import app
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Windows CMD 默认可能是非 UTF-8 代码页，避免中文 print 报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    from sqlalchemy import inspect, text

    from app.core.config import settings
    from app.db.database import engine

    print(
        f"[OK] config loaded: host={settings.db_host} "
        f"port={settings.db_port} user={settings.db_user} db={settings.db_name}"
    )
    # Do not print password

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Engine connected (SELECT 1)")
    except Exception as exc:  # noqa: BLE001 - show real error to developer
        print("[FAIL] Cannot connect to MySQL. Check:")
        print("  1) MySQL service is running")
        print("  2) Database class_management exists (utf8mb4)")
        print("  3) backend/.env DB_USER / DB_PASSWORD / DB_NAME are correct")
        print(f"  detail: {exc}")
        return 1

    expected_tables = ["users", "teachers", "course_categories", "courses"]
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [name for name in expected_tables if name not in existing]

    if missing:
        print(f"[WARN] Connected, but missing tables: {', '.join(missing)}")
        print("       Run: python -m alembic upgrade head")
        return 2

    print("[OK] core tables exist: users, teachers, course_categories, courses")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
