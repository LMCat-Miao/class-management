"""
学生表 ORM（students）。

统计字段（learn_course_count 等）为历史展示快照，不因 enrollments 为空而清零。
recent_courses_json 仅作 API recentCourses 展示快照，不得当作选课关系。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Date, DateTime, SmallInteger, String, func
from sqlalchemy.dialects.mysql import INTEGER, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="主键",
    )
    student_no: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="学号，对应 API studentNo",
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    avatar: Mapped[str] = mapped_column(
        String(512), nullable=False, default="", server_default="", comment="头像 URL"
    )
    class_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", server_default="", comment="班级"
    )
    phone: Mapped[str] = mapped_column(
        String(32), nullable=False, default="", server_default="", comment="手机号"
    )
    learn_course_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="历史学习课程数快照",
    )
    finish_course_count: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="历史完成课程数快照",
    )
    progress: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0", comment="学习进度 0-100"
    )
    avg_completion: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0", comment="平均完成率 0-100"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1", comment="1=正常 0=停用"
    )
    registered_at: Mapped[date] = mapped_column(Date, nullable=False, comment="注册日期")
    recent_courses_json: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
        comment="recentCourses 展示快照（课程名列表），非选课关系",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
