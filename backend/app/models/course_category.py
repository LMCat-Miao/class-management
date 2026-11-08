"""
课程分类表 ORM 模型（course_categories）。

固定五种：前端 / AI / Python / 算法 / Java。
后续 Service 层会限制课程只能引用这些分类。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course


class CourseCategory(Base):
    """课程分类字典表。"""

    __tablename__ = "course_categories"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="主键",
    )
    name: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        comment="分类中文名，API 仍返回该字符串",
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="排序，数值越小越靠前",
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

    courses: Mapped[list["Course"]] = relationship(back_populates="category")
