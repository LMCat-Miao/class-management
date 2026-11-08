"""
认证相关的用户信息组装与教师账号状态校验。

说明：
- 数据库 User 模型不含 roles / permissions / teacherId；
- 这些字段按「单角色 → 权限常量」与 teachers 表关联在响应层组装，
  以保持前端 userInfo 契约不变。
- teacher 登录与受保护请求均要求：存在教师档案且 status=1。
"""

from __future__ import annotations

from app.core.permissions import ADMIN_PERMISSIONS, TEACHER_PERMISSIONS
from app.models.teacher import Teacher
from app.models.user import User


# 前端可识别的稳定错误标识（勿依赖中文 message）
ERROR_ACCOUNT_DISABLED = "ACCOUNT_DISABLED"


class AuthAccountError(Exception):
    """账号状态不允许访问（登录或请求阶段）。"""

    def __init__(
        self,
        message: str,
        status_code: int = 403,
        *,
        error: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error


def permissions_for_role(role: str) -> list[str]:
    """按角色映射权限码列表（不入库）。"""
    if role == "admin":
        return list(ADMIN_PERMISSIONS)
    if role == "teacher":
        return list(TEACHER_PERMISSIONS)
    return []


def is_teacher_profile_active(teacher: Teacher | None) -> bool:
    """教师档案存在且 status=1。"""
    if teacher is None:
        return False
    try:
        return int(teacher.status) == 1
    except (TypeError, ValueError):
        return False


def assert_teacher_login_allowed(user: User, teacher: Teacher | None) -> None:
    """
    登录阶段：role=teacher 必须有启用中的教师档案。
    失败时抛出 AuthAccountError(status_code=401)，由 Router 转成统一登录失败文案。
    admin 不校验教师表。
    """
    if user.role != "teacher":
        return
    if not is_teacher_profile_active(teacher):
        raise AuthAccountError("用户名或密码错误", status_code=401)


def assert_teacher_request_allowed(user: User, teacher: Teacher | None) -> None:
    """
    受保护请求：role=teacher 必须仍有启用中的教师档案。
    否则 403（Token 本身仍有效，但账号状态不允许）。
    admin 不校验教师表。
    """
    if user.role != "teacher":
        return
    if not is_teacher_profile_active(teacher):
        raise AuthAccountError(
            "账号已停用或不可用",
            status_code=403,
            error=ERROR_ACCOUNT_DISABLED,
        )


def build_user_info(user: User, teacher: Teacher | None = None) -> dict:
    """
    组装前端契约 userInfo（不含 password_hash）。

    teacherId 必须是 teachers.id；管理员无档案时不返回该字段。
    仅当教师档案启用时附带 teacherId（停用账号不会走到成功登录/鉴权路径）。
    """
    info: dict = {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "roles": [user.role],
        "permissions": permissions_for_role(user.role),
    }
    # admin 可附带关联档案；teacher 仅在启用档案时附带（调用方已保证）
    if teacher is not None and (
        user.role != "teacher" or is_teacher_profile_active(teacher)
    ):
        info["teacherId"] = teacher.id
    return info
