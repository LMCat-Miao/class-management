"""
资源只读查询：MySQL resources + courses 名称 + SQL 分页。

权限过滤在 SQL WHERE 中完成，不先全量加载再 Python 过滤。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.resource import Resource
from app.services.paging import normalize_page, page_payload
from app.services.resource_access import (
    ResourceAccessError,
    assert_can_manage_course_resources,
    get_course_for_resource,
    parse_course_id,
    teacher_owned_course_ids,
)


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size / 1024 / 1024:.1f}MB"


def serialize_resource(row: Resource, course_name: str = "") -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "type": row.type,
        "courseId": row.course_id,
        "courseName": course_name,
        "size": format_size(int(row.size or 0)),
        "uploader": row.uploader or "",
        "uploadedAt": row.uploaded_at.strftime("%Y-%m-%d %H:%M") if row.uploaded_at else "",
        "status": int(row.status),
    }


def list_resources_for_course(db: Session, course_id: int) -> list[dict]:
    course = db.get(Course, course_id)
    course_name = course.name if course else ""
    rows = db.scalars(
        select(Resource)
        .where(Resource.course_id == course_id)
        .order_by(Resource.id.asc())
    ).all()
    return [serialize_resource(r, course_name) for r in rows]


def list_resources_page(
    db: Session,
    *,
    user: dict,
    name: str | None = None,
    type_filter: str | None = None,
    course_id_raw: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    page, page_size = normalize_page(page, page_size)
    role = user.get("role")
    course_id = parse_course_id(course_id_raw)

    filters = []

    if role == "admin":
        if course_id is not None:
            get_course_for_resource(db, course_id)
            filters.append(Resource.course_id == course_id)
    elif role == "teacher":
        tid = user.get("teacherId")
        if tid is None:
            raise ResourceAccessError("无权限访问", status_code=403)
        if course_id is not None:
            course = get_course_for_resource(db, course_id)
            assert_can_manage_course_resources(user, course)
            filters.append(Resource.course_id == course_id)
        else:
            allowed = teacher_owned_course_ids(db, int(tid))
            if not allowed:
                return page_payload([], 0, page, page_size)
            filters.append(Resource.course_id.in_(allowed))
    else:
        raise ResourceAccessError("无权限访问", status_code=403)

    if name:
        filters.append(Resource.name.contains(name))
    if type_filter:
        filters.append(Resource.type == type_filter)

    count_stmt = select(func.count(Resource.id))
    # 联表取 courseName，避免页内再查课程
    list_stmt = (
        select(Resource, Course.name)
        .join(Course, Course.id == Resource.course_id)
        .order_by(Resource.id.desc())
    )
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)

    total = int(db.scalar(count_stmt) or 0)
    rows = db.execute(
        list_stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [serialize_resource(r, course_name or "") for r, course_name in rows]
    return page_payload(items, total, page, page_size)


def get_resource_row(db: Session, resource_id: int) -> Resource | None:
    return db.get(Resource, resource_id)
