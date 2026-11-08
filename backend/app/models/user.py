"""
用户表 ORM 模型（users）。

说明：
- 只存单角色 role（admin / teacher），不存 permissions / roles 数组。
- 密码只存 password_hash（bcrypt），绝不存明文。
- 本阶段不增加 status 字段（与已确认的库表设计一致）。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.teacher import Teacher


class User(Base):
    """登录账号。管理员可以没有关联的 Teacher 档案。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="主键",
    )
    username: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="登录用户名，唯一",
    )
    nickname: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
        comment="昵称",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt 密码哈希，禁止返回给前端",
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="单角色：admin 或 teacher",
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

    # relationship：在 Python 侧建立对象导航，不单独占一列。
    # 外键定义在 teachers.user_id 上；这里是反向引用。
    teacher: Mapped[Optional["Teacher"]] = relationship(
        back_populates="user",
        uselist=False,
    )
