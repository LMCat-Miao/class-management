"""
课程表 ORM 模型（courses）。

外键：
- category_id → course_categories.id，ON DELETE RESTRICT（有课则禁止删分类）
- teacher_id → teachers.id，ON DELETE RESTRICT（有课则禁止删教师）

章节：
- 数据库列名 chapters_json（MySQL JSON）
- API 对外字段名仍为 chapters（由后续 Service / Schema 转换）
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import INTEGER, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course_category import CourseCategory
    from app.models.teacher import Teacher


class Course(Base):
    """课程主表。"""

    __tablename__ = "courses"
    __table_args__ = (
        # 数据库层约束：完成率必须在 0～100（Service 层还会再校验一次）
        CheckConstraint(
            "completion_rate >= 0 AND completion_rate <= 100",
            name="ck_courses_completion_rate",
        ),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="主键",
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="课程名称",
    )
    cover: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="",
        server_default="",
        comment="封面 URL",
    )
    category_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("course_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="分类外键",
    )
    teacher_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="授课教师外键",
    )
    difficulty: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="初级",
        server_default="初级",
        comment="难度：初级/中级/高级",
    )
    duration: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="时长（小时）",
    )
    student_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="学生数量（展示字段）",
    )
    learn_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="学习人数（展示/排行字段）",
    )
    completion_rate: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="完成率 0～100 的整数",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="1=上架，0=下架",
    )
    # MySQL 8.x：TEXT 不能有数据库级 DEFAULT，空串仅用 Python 侧 default
    intro: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="课程简介",
    )
    # MySQL 8.x：JSON 同样不宜设 server_default；未传章节时由 default=list 写入 []
    # API 对外字段名仍叫 chapters（Service 层转换）
    chapters_json: Mapped[Any] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="章节数组，如 [{id, title}, ...]；API 对外叫 chapters",
    )
    created_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="创建日期；API 返回 YYYY-MM-DD 字符串 createdAt",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    category: Mapped["CourseCategory"] = relationship(back_populates="courses")
    teacher: Mapped["Teacher"] = relationship(back_populates="courses")
