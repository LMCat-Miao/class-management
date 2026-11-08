"""
选课关系 API（4.3.3.3）。

仅 admin 可创建/退选/改状态；teacher 不可自行选课。
学习统计字段仍为历史快照，本接口不改写。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.deps import require_roles
from app.services.enrollment_service import (
    EnrollmentError,
    create_enrollment,
    drop_enrollment,
    list_enrollments_for_course,
    list_enrollments_for_student,
    set_enrollment_status,
)

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


class EnrollmentCreateBody(BaseModel):
    studentId: int
    courseId: int


class EnrollmentStatusBody(BaseModel):
    status: int


@router.post("")
def create_enrollment_api(
    body: EnrollmentCreateBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = create_enrollment(db, body.studentId, body.courseId)
    except EnrollmentError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)


@router.get("/student/{student_id}")
def enrollments_by_student(
    student_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        items = list_enrollments_for_student(db, student_id)
    except EnrollmentError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(items)


@router.get("/course/{course_id}")
def enrollments_by_course(
    course_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        items = list_enrollments_for_course(db, course_id)
    except EnrollmentError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(items)


@router.put("/{enrollment_id}/drop")
def drop_enrollment_api(
    enrollment_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = drop_enrollment(db, enrollment_id)
    except EnrollmentError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)


@router.put("/{enrollment_id}/status")
def update_enrollment_status_api(
    enrollment_id: int,
    body: EnrollmentStatusBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        item = set_enrollment_status(db, enrollment_id, body.status)
    except EnrollmentError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)
