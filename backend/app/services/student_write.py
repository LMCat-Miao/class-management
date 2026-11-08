"""
学生写入（4.3.3.2）：MySQL students CRUD。

学习统计字段为历史快照，创建时默认 0；更新时未传字段不得清空。
progress / avgCompletion 在 Service 层校验 0–100。
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.student import Student
from app.services.student_query import get_student_by_id, serialize_student


class StudentWriteError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


ALLOWED_STATUS = frozenset({0, 1})


def normalize_status(raw: Any) -> int:
    if isinstance(raw, bool):
        raise StudentWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise StudentWriteError("状态值无效，仅允许 0 或 1", status_code=400) from exc
    if isinstance(raw, float) and float(raw) != float(value):
        raise StudentWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    if value not in ALLOWED_STATUS:
        raise StudentWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    return value


def normalize_percent(raw: Any, field_label: str) -> int:
    if isinstance(raw, bool):
        raise StudentWriteError(f"{field_label} 无效，须为 0–100 的整数", status_code=400)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise StudentWriteError(f"{field_label} 无效，须为 0–100 的整数", status_code=400) from exc
    if isinstance(raw, float) and float(raw) != float(value):
        raise StudentWriteError(f"{field_label} 无效，须为 0–100 的整数", status_code=400)
    if value < 0 or value > 100:
        raise StudentWriteError(f"{field_label} 无效，须为 0–100 的整数", status_code=400)
    return value


def create_student(db: Session, data: Any) -> dict:
    name = (getattr(data, "name", None) or "").strip()
    if not name:
        raise StudentWriteError("请输入学生姓名", status_code=400)

    student_no = (getattr(data, "studentNo", None) or "").strip()
    status_raw = getattr(data, "status", None)
    status = 1 if status_raw is None else normalize_status(status_raw)

    student = Student(
        name=name,
        avatar=getattr(data, "avatar", None) or "",
        student_no=student_no or "",  # 占位，flush 后若空则用 S{id}
        class_name=getattr(data, "className", None) or "",
        phone=getattr(data, "phone", None) or "",
        learn_course_count=0,
        finish_course_count=0,
        progress=0,
        avg_completion=0,
        status=status,
        registered_at=date.today(),
        recent_courses_json=[],
    )

    try:
        db.add(student)
        db.flush()
        if not student_no:
            student.student_no = f"S{student.id}"
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise StudentWriteError("学号已存在", status_code=400) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise StudentWriteError("学生创建失败", status_code=500) from exc

    created = get_student_by_id(db, student.id)
    if not created:
        raise StudentWriteError("学生创建后读取失败", status_code=500)
    return created


def update_student(db: Session, student_id: int, update_data: dict[str, Any]) -> dict:
    student = db.get(Student, student_id)
    if not student:
        raise StudentWriteError("学生不存在", status_code=404)

    data = {k: v for k, v in update_data.items() if k != "id"}

    if "name" in data:
        name = (data["name"] or "").strip() if data["name"] is not None else ""
        if not name:
            raise StudentWriteError("请输入学生姓名", status_code=400)
        student.name = name
    if "avatar" in data:
        student.avatar = "" if data["avatar"] is None else str(data["avatar"])
    if "studentNo" in data:
        sno = ("" if data["studentNo"] is None else str(data["studentNo"])).strip()
        if not sno:
            raise StudentWriteError("学号不能为空", status_code=400)
        student.student_no = sno
    if "className" in data:
        student.class_name = "" if data["className"] is None else str(data["className"])
    if "phone" in data:
        student.phone = "" if data["phone"] is None else str(data["phone"])
    if "status" in data and data["status"] is not None:
        student.status = normalize_status(data["status"])
    if "progress" in data and data["progress"] is not None:
        student.progress = normalize_percent(data["progress"], "progress")
    if "avgCompletion" in data and data["avgCompletion"] is not None:
        student.avg_completion = normalize_percent(data["avgCompletion"], "avgCompletion")
    if "learnCourseCount" in data and data["learnCourseCount"] is not None:
        student.learn_course_count = max(0, int(data["learnCourseCount"]))
    if "finishCourseCount" in data and data["finishCourseCount"] is not None:
        student.finish_course_count = max(0, int(data["finishCourseCount"]))
    if "recentCourses" in data:
        raw = data["recentCourses"]
        student.recent_courses_json = list(raw) if isinstance(raw, list) else []

    try:
        db.add(student)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise StudentWriteError("学号已存在", status_code=400) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise StudentWriteError("学生更新失败", status_code=500) from exc

    updated = get_student_by_id(db, student.id)
    if not updated:
        raise StudentWriteError("学生更新后读取失败", status_code=500)
    return updated


def update_student_status(db: Session, student_id: int, status: int) -> dict:
    student = db.get(Student, student_id)
    if not student:
        raise StudentWriteError("学生不存在", status_code=404)

    student.status = normalize_status(status)
    try:
        db.add(student)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise StudentWriteError("学生状态更新失败", status_code=500) from exc

    return serialize_student(student)
