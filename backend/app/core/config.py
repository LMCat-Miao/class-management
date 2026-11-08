"""
应用配置。

使用 pydantic-settings 从环境变量 / .env 读取配置。
数据库密码等敏感信息只放在 .env 中，不要写进代码仓库。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仅用于本地开发的默认值；生产环境禁止使用（见 validate_settings）。
DEV_SECRET_KEY = "class-management-dev-secret-change-me"

# 视为「生产」的 APP_ENV 取值（大小写不敏感）
_PRODUCTION_ENVS = frozenset({"production", "prod"})


class Settings(BaseSettings):
    """全局配置项。优先读取环境变量，其次读取 backend 目录下的 .env 文件。"""

    model_config = SettingsConfigDict(
        # 相对「运行时的当前工作目录」查找 .env；建议在 backend 目录下启动命令
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Course Management API"
    # development：可使用开发默认 SECRET_KEY；production/prod：必须显式配置强随机 SECRET_KEY
    app_env: str = "development"
    secret_key: str = DEV_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ---------- MySQL 连接（通过 .env 配置，禁止硬编码真实密码）----------
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "class_management"

    # 连接池基础参数（SQLAlchemy Engine 使用）
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # ---------- 资源上传（相对 backend 工作目录）----------
    upload_dir: str = "uploads"
    upload_max_bytes: int = 50 * 1024 * 1024  # 50MB
    # AI PDF 解析读入内存，单独限制以免超大文件占满内存
    ai_pdf_max_bytes: int = 10 * 1024 * 1024  # 10MB

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in _PRODUCTION_ENVS

    @property
    def database_url(self) -> str:
        """
        拼出 SQLAlchemy 使用的数据库 URL。

        驱动说明：
        - 使用 PyMySQL 作为 DBAPI（纯 Python，Windows 安装方便）
        - 格式：mysql+pymysql://用户:密码@主机:端口/库名?charset=utf8mb4
        """
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )


class ConfigSecurityError(RuntimeError):
    """配置安全校验失败（启动阶段抛出；消息中不得包含 Secret 明文）。"""


def validate_settings(cfg: Settings) -> None:
    """
    校验配置安全性。

    - 开发环境：允许使用 DEV_SECRET_KEY。
    - 生产环境（APP_ENV=production|prod）：必须提供非空且非开发默认值的 SECRET_KEY。
    """
    if not cfg.is_production:
        return

    key = (cfg.secret_key or "").strip()
    if not key:
        raise ConfigSecurityError(
            "生产环境（APP_ENV=production）必须通过环境变量 SECRET_KEY 配置 JWT 密钥，"
            "不能为空。"
        )
    if key == DEV_SECRET_KEY:
        raise ConfigSecurityError(
            "生产环境（APP_ENV=production）禁止使用开发默认 JWT 密钥。"
            "请设置强随机的 SECRET_KEY（勿将密钥写入 Git 或日志）。"
        )


@lru_cache
def get_settings() -> Settings:
    """缓存 Settings 单例；加载后立即做生产环境 Secret 校验。"""
    cfg = Settings()
    validate_settings(cfg)
    return cfg


# 兼容原有 `from app.core.config import settings` 写法（导入时即校验）
settings = get_settings()
