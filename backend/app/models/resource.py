"""
课程资源元数据表 resources。

文件二进制不入库；file_path 存相对路径，旧演示数据可为 NULL。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.user import User


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True, comment="主键"
    )
    course_id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="所属课程",
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="其他", comment="资源类型")
    size: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="文件字节数",
    )
    uploader: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", server_default="", comment="上传人展示名"
    )
    uploader_user_id: Mapped[Optional[int]] = mapped_column(
        INTEGER(unsigned=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="上传用户，可空",
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="上传时间"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1", comment="1=正常 0=停用"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="相对上传根目录的路径，可空"
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

    course: Mapped["Course"] = relationship()
    uploader_user: Mapped[Optional["User"]] = relationship()
