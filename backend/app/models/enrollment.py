"""
选课关系表 enrollments：students ↔ courses 多对多。

不得根据 recentCourses 课程名自动生成记录。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, UniqueConstraint, func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.student import Student


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_enrollments_student_course"),
    )

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="主键"
    )
    student_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="学生外键",
    )
    course_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="课程外键",
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="1=在读 0=退选",
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="选课时间"
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

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship()
