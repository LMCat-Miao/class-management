"""
教师管理（4.3.2.3）：MySQL teachers；统计来自 MySQL courses。
仅 admin。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.deps import require_roles
from app.services.teacher_query import get_teacher_by_id, list_teachers_page
from app.services.teacher_write import (
    TeacherWriteError,
    create_teacher as create_teacher_db,
    delete_teacher as delete_teacher_db,
    update_teacher as update_teacher_db,
)

router = APIRouter(prefix="/teacher", tags=["teacher"])


class TeacherBody(BaseModel):
    name: str
    avatar: str | None = ""
    phone: str | None = ""
    email: str | None = ""
    title: str | None = "讲师"
    status: int | None = 1


@router.get("/list")
def list_teachers(
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    data = list_teachers_page(
        db, name=name, status=status, page=page, page_size=pageSize
    )
    return ok(data)


@router.get("/{teacher_id}")
def teacher_detail(
    teacher_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        return fail("教师不存在", status_code=404)
    return ok(teacher)


@router.post("")
def create_teacher(
    body: TeacherBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        data = create_teacher_db(db, body)
    except TeacherWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int,
    body: TeacherBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    payload = body.model_dump(exclude_unset=True)
    try:
        data = update_teacher_db(db, teacher_id, payload)
    except TeacherWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        delete_teacher_db(db, teacher_id)
    except TeacherWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(True)
