from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.deps import get_current_user, require_roles
from app.services.course_query import (
    CourseQueryError,
    can_view_course,
    get_course_by_id,
    list_courses_page,
)
from app.services.resource_query import list_resources_for_course

router = APIRouter(prefix="/course", tags=["course"])


class CourseBody(BaseModel):
    name: str
    cover: str | None = None
    category: str | None = None
    teacherId: int | None = None
    teacher: str | None = None
    difficulty: str | None = "初级"
    duration: int | None = 0
    # bool 放在 int 前，避免 True/False 被收成 1/0；非法值由 Service normalize_course_status 返回 400
    status: bool | int | None = 1
    intro: str | None = ""
    chapters: list[dict[str, Any]] | None = None


class StatusBody(BaseModel):
    """上下架请求体；合法值 0/1 由 Service 校验（保证非法值返回 HTTP 400，而非 422）。"""

    status: int


@router.get("/list")
def list_courses(
    name: str | None = None,
    category: str | None = None,
    teacher: str | None = None,
    status: str | None = None,
    startDate: str | None = None,
    endDate: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    课程列表：从 MySQL 读取。

    4.3.1.2：teacher 必须有有效 teacherId，否则 403（禁止无档案时返回全量）。
    """
    try:
        data = list_courses_page(
            db,
            user=user,
            name=name,
            category=category,
            teacher=teacher,
            status=status,
            start_date=startDate,
            end_date=endDate,
            page=page,
            page_size=pageSize,
        )
    except CourseQueryError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.get("/{course_id}")
def course_detail(
    course_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    课程详情：主体与 resources 均从 MySQL 读取。

    权限：admin 全部；teacher 仅本人名下课程（teacherId = teachers.id）。
    先 404（不存在），再 403（存在但无归属），避免用 404 掩盖越权。
    """
    course = get_course_by_id(db, course_id)
    if not course:
        return fail("课程不存在", status_code=404)
    if not can_view_course(user, course):
        return fail("无权限访问", code=403, status_code=403)
    related = list_resources_for_course(db, course_id)
    return ok({**course, "resources": related})


@router.post("")
def create_course(
    body: CourseBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """
    新增课程：写入 MySQL。
    仍仅管理员可操作；请求/响应字段保持不变。
    """
    _ = user
    from app.services.course_write import CourseWriteError, create_course as create_course_db

    try:
        data = create_course_db(db, body)
    except CourseWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.put("/{course_id}")
def update_course(
    course_id: int,
    body: CourseBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """
    编辑课程（4.2.2）：部分更新写入 MySQL。
    使用 model_dump(exclude_unset=True)，未传字段保持库中原值。
    """
    _ = user
    from app.services.course_write import CourseWriteError, update_course as update_course_db

    payload = body.model_dump(exclude_unset=True)
    try:
        data = update_course_db(db, course_id, payload)
    except CourseWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """
    删除课程：有选课则 409；否则删除 MySQL 中课程与资源元数据，commit 后再尽量清理磁盘文件。
    成功响应仍为 data=True。
    """
    _ = user
    from app.services.course_write import CourseWriteError, delete_course as delete_course_db

    try:
        delete_course_db(db, course_id)
    except CourseWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(True)


@router.put("/{course_id}/status")
def update_status(
    course_id: int,
    body: StatusBody,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    """
    上下架：更新 MySQL courses.status。
    成功响应 data 仍为完整课程对象（与 list/detail 字段一致）。
    """
    _ = user
    from app.services.course_write import CourseWriteError, update_course_status

    try:
        data = update_course_status(db, course_id, body.status)
    except CourseWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)
