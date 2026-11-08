"""
学生管理（4.3.3.2）：MySQL students。

- admin：全部读写
- teacher：仅通过 enrollments → courses.teacher_id 查看自己课程下学生；无写权限
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.deps import get_current_user, require_roles
from app.services.student_query import StudentQueryError, get_student_by_id, list_students_page
from app.services.student_write import (
    StudentWriteError,
    create_student,
    update_student,
    update_student_status,
)

router = APIRouter(prefix="/student", tags=["student"])


class StudentBody(BaseModel):
    name: str
    avatar: str | None = ""
    studentNo: str | None = None
    className: str | None = ""
    phone: str | None = ""
    status: int | None = 1
    progress: int | None = None
    avgCompletion: int | None = None
    learnCourseCount: int | None = None
    finishCourseCount: int | None = None
    recentCourses: list[str] | None = None


class StatusBody(BaseModel):
    status: int


@router.get("/list")
def list_students(
    name: str | None = None,
    studentNo: str | None = None,
    className: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = list_students_page(
            db,
            user=user,
            name=name,
            student_no=studentNo,
            class_name=className,
            status=status,
            page=page,
            page_size=pageSize,
        )
    except StudentQueryError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.get("/{student_id}")
def student_detail(
    student_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        student = get_student_by_id(db, student_id, user=user)
    except StudentQueryError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    if not student:
        return fail("学生不存在", status_code=404)
    return ok(student)


@router.post("")
def create_student_api(
    body: StudentBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = create_student(db, body)
    except StudentWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)


@router.put("/{student_id}")
def update_student_api(
    student_id: int,
    body: StudentBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = update_student(db, student_id, body.model_dump(exclude_unset=True))
    except StudentWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)


@router.put("/{student_id}/status")
def update_status(
    student_id: int,
    body: StatusBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = update_student_status(db, student_id, body.status)
    except StudentWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)
