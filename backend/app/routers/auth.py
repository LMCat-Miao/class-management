"""
认证路由：登录 / 用户信息 / 登出。

登录：校验 users +（teacher 角色时）启用中的教师档案。
登出：客户端会话清理语义；本接口不实现服务端 Token 黑名单或即时撤销。
登录仅返回 accessToken（无 refresh 换发接口，故不再签发 refreshToken）。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.core.security import create_access_token, verify_password
from app.db.database import get_db
from app.deps import get_current_user
from app.models.teacher import Teacher
from app.models.user import User
from app.services.auth_user import (
    AuthAccountError,
    assert_teacher_login_allowed,
    build_user_info,
)

router = APIRouter(tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    username = body.username.strip()
    password = body.password.strip()

    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        # 统一文案，避免枚举用户是否存在
        return fail("用户名或密码错误", status_code=401)

    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    try:
        assert_teacher_login_allowed(user, teacher)
    except AuthAccountError:
        # 无档案 / 停用：同样不泄露内部原因
        return fail("用户名或密码错误", status_code=401)

    user_info = build_user_info(user, teacher)
    access = create_access_token(user.id, user.role)
    return ok(
        {
            "accessToken": access,
            "userInfo": user_info,
        }
    )


@router.get("/user/info")
def user_info(user: dict = Depends(get_current_user)):
    # get_current_user 已含教师 status 校验
    return ok(user)


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    """
    登出：确认当前会话身份后返回成功。

    语义：服务端不撤销 JWT；客户端须清除 accessToken 与本地用户状态。
    Token 在过期前若仍被持有，仍可通过签名校验，但教师停用会在 get_current_user 被拒绝。
    """
    _ = user
    return ok(True)
