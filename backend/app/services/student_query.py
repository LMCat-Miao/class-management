"""
学生只读查询：MySQL students + SQL 分页。

teacher 通过 enrollments → courses.teacher_id 过滤；
无教师档案 → 403；有档案但无选课 → 空列表（非 403）。
同一学生经多门课关联同一教师时 DISTINCT，不重复返回。
"""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.teacher import Teacher
from app.services.paging import normalize_page, page_payload


class StudentQueryError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def serialize_student(student: Student) -> dict:
    recent = student.recent_courses_json
    if recent is None:
        recent_courses: list = []
    elif isinstance(recent, list):
        recent_courses = list(recent)
    else:
        recent_courses = []

    return {
        "id": student.id,
        "name": student.name,
        "avatar": student.avatar or "",
        "studentNo": student.student_no,
        "className": student.class_name or "",
        "phone": student.phone or "",
        "learnCourseCount": int(student.learn_course_count or 0),
        "finishCourseCount": int(student.finish_course_count or 0),
        "progress": int(student.progress or 0),
        "status": int(student.status),
        "registeredAt": student.registered_at.isoformat() if student.registered_at else "",
        "recentCourses": recent_courses,
        "avgCompletion": int(student.avg_completion or 0),
    }


def resolve_teacher_profile(db: Session, user: dict) -> Teacher:
    """teacher 必须有 teachers 档案；否则 403。"""
    tid = user.get("teacherId")
    if tid is None:
        raise StudentQueryError("无权限访问", status_code=403)
    teacher = db.get(Teacher, int(tid))
    if not teacher:
        raise StudentQueryError("无权限访问", status_code=403)
    return teacher


def student_ids_for_teacher(db: Session, teacher_id: int) -> set[int]:
    """在读选课（status=1）且课程归属该教师的学生 id（去重）。"""
    rows = db.scalars(
        select(Enrollment.student_id)
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Course.teacher_id == int(teacher_id),
            Enrollment.status == 1,
        )
        .distinct()
    ).all()
    return {int(x) for x in rows}


def teacher_can_view_student(db: Session, teacher_id: int, student_id: int) -> bool:
    exists = db.scalar(
        select(Enrollment.id)
        .join(Course, Course.id == Enrollment.course_id)
        .where(
            Enrollment.student_id == int(student_id),
            Course.teacher_id == int(teacher_id),
            Enrollment.status == 1,
        )
        .limit(1)
    )
    return exists is not None


def get_student_by_id(
    db: Session,
    student_id: int,
    *,
    user: dict | None = None,
) -> dict | None:
    student = db.get(Student, student_id)
    if not student:
        return None

    if user is not None and user.get("role") == "teacher":
        teacher = resolve_teacher_profile(db, user)
        if not teacher_can_view_student(db, teacher.id, student_id):
            raise StudentQueryError("无权限访问", status_code=403)

    return serialize_student(student)


def _apply_student_filters(
    stmt: Select,
    *,
    name: str | None,
    student_no: str | None,
    class_name: str | None,
    status: str | None,
) -> Select:
    if name:
        stmt = stmt.where(Student.name.contains(name))
    if student_no:
        stmt = stmt.where(Student.student_no.contains(student_no))
    if class_name:
        stmt = stmt.where(Student.class_name.contains(class_name))
    if status is not None and status != "":
        stmt = stmt.where(Student.status == int(status))
    return stmt


def list_students_page(
    db: Session,
    *,
    user: dict,
    name: str | None = None,
    student_no: str | None = None,
    class_name: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    page, page_size = normalize_page(page, page_size)
    role = user.get("role")

    if role == "admin":
        base = select(Student)
        count_base = select(func.count(Student.id))
    elif role == "teacher":
        teacher = resolve_teacher_profile(db, user)
        # 子查询去重，避免多课关联导致重复学生
        scoped_ids = (
            select(Enrollment.student_id)
            .join(Course, Course.id == Enrollment.course_id)
            .where(
                Course.teacher_id == int(teacher.id),
                Enrollment.status == 1,
            )
            .distinct()
        )
        probe = db.scalar(scoped_ids.limit(1))
        if probe is None:
            return page_payload([], 0, page, page_size)
        base = select(Student).where(Student.id.in_(scoped_ids))
        count_base = select(func.count(Student.id)).where(Student.id.in_(scoped_ids))
    else:
        raise StudentQueryError("无权限访问", status_code=403)

    filtered = _apply_student_filters(
        base,
        name=name,
        student_no=student_no,
        class_name=class_name,
        status=status,
    )
    count_filtered = _apply_student_filters(
        count_base,
        name=name,
        student_no=student_no,
        class_name=class_name,
        status=status,
    )

    total = int(db.scalar(count_filtered) or 0)
    rows = list(
        db.scalars(
            filtered.order_by(Student.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return page_payload([serialize_student(s) for s in rows], total, page, page_size)
