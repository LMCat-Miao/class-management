"""
选课关系（4.3.3.3）。

统计字段 learnCourseCount 等仍为历史快照，本模块不因选课增删自动改写。
退选保留记录并将 status 置 0；再次选课恢复 status=1，不插入重复行。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student


class EnrollmentError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def serialize_enrollment(row: Enrollment, *, student_name: str = "", course_name: str = "") -> dict:
    return {
        "id": row.id,
        "studentId": row.student_id,
        "courseId": row.course_id,
        "status": int(row.status),
        "enrolledAt": row.enrolled_at.strftime("%Y-%m-%d %H:%M:%S") if row.enrolled_at else "",
        "studentName": student_name,
        "courseName": course_name,
    }


def create_enrollment(db: Session, student_id: int, course_id: int) -> dict:
    student = db.get(Student, student_id)
    if not student:
        raise EnrollmentError("学生不存在", status_code=404)
    course = db.get(Course, course_id)
    if not course:
        raise EnrollmentError("课程不存在", status_code=404)

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing:
        if int(existing.status) == 1:
            raise EnrollmentError("选课关系已存在", status_code=400)
        # 退选后再次选课：恢复 status，不插新行
        existing.status = 1
        existing.enrolled_at = datetime.now()
        try:
            db.add(existing)
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise EnrollmentError("选课失败", status_code=500) from exc
        return serialize_enrollment(
            existing, student_name=student.name, course_name=course.name
        )

    row = Enrollment(
        student_id=student_id,
        course_id=course_id,
        status=1,
        enrolled_at=datetime.now(),
    )
    try:
        db.add(row)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EnrollmentError("选课关系已存在", status_code=400) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise EnrollmentError("选课失败", status_code=500) from exc

    db.refresh(row)
    return serialize_enrollment(row, student_name=student.name, course_name=course.name)


def drop_enrollment(db: Session, enrollment_id: int) -> dict:
    """退选：status=0，保留记录。"""
    row = db.get(Enrollment, enrollment_id)
    if not row:
        raise EnrollmentError("选课记录不存在", status_code=404)
    row.status = 0
    try:
        db.add(row)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise EnrollmentError("退选失败", status_code=500) from exc

    student = db.get(Student, row.student_id)
    course = db.get(Course, row.course_id)
    return serialize_enrollment(
        row,
        student_name=student.name if student else "",
        course_name=course.name if course else "",
    )


def set_enrollment_status(db: Session, enrollment_id: int, status: int) -> dict:
    if status not in (0, 1):
        raise EnrollmentError("选课状态无效，仅允许 0 或 1", status_code=400)
    row = db.get(Enrollment, enrollment_id)
    if not row:
        raise EnrollmentError("选课记录不存在", status_code=404)
    row.status = status
    if status == 1:
        row.enrolled_at = datetime.now()
    try:
        db.add(row)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise EnrollmentError("选课状态更新失败", status_code=500) from exc

    student = db.get(Student, row.student_id)
    course = db.get(Course, row.course_id)
    return serialize_enrollment(
        row,
        student_name=student.name if student else "",
        course_name=course.name if course else "",
    )


def list_enrollments_for_student(db: Session, student_id: int) -> list[dict]:
    if not db.get(Student, student_id):
        raise EnrollmentError("学生不存在", status_code=404)
    # JOIN 一次取课程名，避免循环 db.get（N+1）
    rows = db.execute(
        select(Enrollment, Course.name)
        .outerjoin(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == student_id)
        .order_by(Enrollment.id.asc())
    ).all()
    return [
        serialize_enrollment(row, course_name=course_name or "")
        for row, course_name in rows
    ]


def list_enrollments_for_course(db: Session, course_id: int) -> list[dict]:
    if not db.get(Course, course_id):
        raise EnrollmentError("课程不存在", status_code=404)
    rows = db.execute(
        select(Enrollment, Student.name)
        .outerjoin(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.course_id == course_id)
        .order_by(Enrollment.id.asc())
    ).all()
    return [
        serialize_enrollment(row, student_name=student_name or "")
        for row, student_name in rows
    ]
