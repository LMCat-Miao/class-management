"""
FastAPI 依赖：当前用户、角色校验。

每次受保护请求从 MySQL 重新加载用户；teacher 还必须有启用中的教师档案（status=1）。
停用教师即使 Token 未过期也会被拒绝（HTTP 403）。
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.teacher import Teacher
from app.models.user import User
from app.services.auth_user import (
    AuthAccountError,
    assert_teacher_request_allowed,
    build_user_info,
)

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    解析 Bearer Access Token，按 sub（users.id）查询 MySQL，返回 userInfo 形态字典。

    - Token 无效/过期/类型错误/用户不存在 → 401
    - role=teacher 但无档案或 status≠1 → 403
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或令牌缺失",
        )
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
        )

    raw_sub = payload.get("sub")
    try:
        user_id = int(raw_sub)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的令牌",
        ) from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    try:
        assert_teacher_request_allowed(user, teacher)
    except AuthAccountError as exc:
        detail: str | dict
        if exc.error:
            detail = {"message": exc.message, "error": exc.error}
        else:
            detail = exc.message
        raise HTTPException(
            status_code=exc.status_code,
            detail=detail,
        ) from exc

    return build_user_info(user, teacher)


def require_roles(*roles: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles and not set(roles) & set(user.get("roles", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问",
            )
        return user

    return checker
