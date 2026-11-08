"""
教师档案表 ORM 模型（teachers）。

外键说明：
- user_id → users.id：可空、唯一。教师登录账号与档案 1:1；
  管理员通常没有教师档案。
- ON DELETE SET NULL：删除用户时，教师档案可保留但解除账号绑定。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.user import User


class Teacher(Base):
    """教师业务档案（与登录用户可选绑定）。"""

    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="主键；API 中的 teacherId 使用本字段，不是 users.id",
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        comment="关联登录用户，可空且唯一",
    )
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="教师姓名",
    )
    avatar: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="",
        server_default="",
        comment="头像 URL",
    )
    phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="",
        server_default="",
        comment="手机号",
    )
    email: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="",
        server_default="",
        comment="邮箱",
    )
    title: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="讲师",
        server_default="讲师",
        comment="职称",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="1=启用，0=停用",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="teacher")
    courses: Mapped[list["Course"]] = relationship(back_populates="teacher")
