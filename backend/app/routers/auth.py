from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.response import fail, ok
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.data.store import USERS, public_user
from app.deps import get_current_user

router = APIRouter(tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login")
def login(body: LoginBody):
    username = body.username.strip()
    password = body.password.strip()
    user = USERS.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        return fail("用户名或密码错误", status_code=401)

    access = create_access_token(username, user["role"])
    refresh = create_refresh_token(username, user["role"])
    return ok(
        {
            "accessToken": access,
            "refreshToken": refresh,
            "userInfo": public_user(user),
        }
    )


@router.get("/user/info")
def user_info(user: dict = Depends(get_current_user)):
    return ok(public_user(user))


@router.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    _ = user
    return ok(True)
