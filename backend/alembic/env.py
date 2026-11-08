"""
Alembic 运行环境。

为什么需要 Alembic？
- 数据库表结构会随需求演进（加字段、加索引、改约束）。
- 用版本化的迁移脚本记录每一次变更，可 upgrade / downgrade，
  比在代码里 create_all 或手工改表更可控、可回滚。

本文件职责：
1. 从 Settings（.env）读取 DATABASE URL，避免密码写进 ini。
2. 导入全部 ORM 模型，让 autogenerate 能对比 metadata。
3. 以 offline / online 两种模式执行迁移。
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# 保证 `import app...` 在 backend 目录下执行时可找到包
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402

# 必须导入 models，才会把表注册到 Base.metadata
import app.models  # noqa: E402, F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 用环境变量中的真实连接串覆盖 alembic.ini 占位符
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式：只生成 SQL，不真正连库（较少使用）。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接 MySQL 并执行迁移（日常使用）。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
