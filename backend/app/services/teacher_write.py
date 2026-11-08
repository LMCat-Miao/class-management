"""
教师写入（4.3.2.3）：MySQL teachers CRUD。
不自动创建 users；有课程关联时禁止删除（409）。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.teacher import Teacher
from app.services.teacher_query import get_teacher_by_id


class TeacherWriteError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def create_teacher(db: Session, data: Any) -> dict:
    name = (getattr(data, "name", None) or "").strip()
    if not name:
        raise TeacherWriteError("请输入教师姓名", status_code=400)

    teacher = Teacher(
        name=name,
        avatar=getattr(data, "avatar", None) or "",
        phone=getattr(data, "phone", None) or "",
        email=getattr(data, "email", None) or "",
        title=getattr(data, "title", None) or "讲师",
        status=1 if getattr(data, "status", None) is None else int(data.status),
        user_id=None,
    )
    try:
        db.add(teacher)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise TeacherWriteError("教师创建失败", status_code=500) from exc

    created = get_teacher_by_id(db, teacher.id)
    if not created:
        raise TeacherWriteError("教师创建后读取失败", status_code=500)
    return created


def update_teacher(db: Session, teacher_id: int, update_data: dict[str, Any]) -> dict:
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise TeacherWriteError("教师不存在", status_code=404)

    data = {k: v for k, v in update_data.items() if k != "id"}

    if "name" in data:
        name = (data["name"] or "").strip() if data["name"] is not None else ""
        if not name:
            raise TeacherWriteError("请输入教师姓名", status_code=400)
        teacher.name = name
    if "avatar" in data:
        teacher.avatar = "" if data["avatar"] is None else str(data["avatar"])
    if "phone" in data:
        teacher.phone = "" if data["phone"] is None else str(data["phone"])
    if "email" in data:
        teacher.email = "" if data["email"] is None else str(data["email"])
    if "title" in data and data["title"] is not None:
        teacher.title = str(data["title"]) or "讲师"
    if "status" in data and data["status"] is not None:
        teacher.status = int(data["status"])

    try:
        db.add(teacher)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise TeacherWriteError("教师更新失败", status_code=500) from exc

    updated = get_teacher_by_id(db, teacher.id)
    if not updated:
        raise TeacherWriteError("教师更新后读取失败", status_code=500)
    return updated


def delete_teacher(db: Session, teacher_id: int) -> bool:
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise TeacherWriteError("教师不存在", status_code=404)

    course_cnt = int(
        db.scalar(
            select(func.count(Course.id)).where(Course.teacher_id == teacher_id)
        )
        or 0
    )
    if course_cnt > 0:
        raise TeacherWriteError(
            "该教师仍有关联课程，无法删除",
            status_code=409,
        )

    try:
        db.delete(teacher)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise TeacherWriteError(
            "该教师仍有关联课程，无法删除",
            status_code=409,
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise TeacherWriteError("教师删除失败", status_code=500) from exc

    return True
