from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Course Management API"
    secret_key: str = "class-management-dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


settings = Settings()
