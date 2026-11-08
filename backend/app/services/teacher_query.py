"""
教师只读查询：MySQL teachers + courses 聚合统计 + SQL 分页。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.teacher import Teacher
from app.services.paging import normalize_page, page_payload


def _course_stats_by_teacher(db: Session, teacher_ids: list[int]) -> dict[int, dict]:
    """批量聚合：courseCount / studentCount / avgCompletion / courses 列表。"""
    if not teacher_ids:
        return {}

    courses = db.scalars(
        select(Course)
        .where(Course.teacher_id.in_(teacher_ids))
        .order_by(Course.id.asc())
    ).all()

    stats: dict[int, dict] = {
        tid: {
            "courseCount": 0,
            "studentCount": 0,
            "avgCompletion": 0,
            "courses": [],
            "courseIds": [],
            "_rates": [],
        }
        for tid in teacher_ids
    }

    for c in courses:
        bucket = stats.get(int(c.teacher_id))
        if not bucket:
            continue
        bucket["courseCount"] += 1
        bucket["studentCount"] += int(c.student_count or 0)
        bucket["_rates"].append(int(c.completion_rate or 0))
        bucket["courseIds"].append(c.id)
        bucket["courses"].append(
            {
                "id": c.id,
                "name": c.name,
                "studentCount": int(c.student_count or 0),
                "completionRate": int(c.completion_rate or 0),
            }
        )

    for tid, bucket in stats.items():
        rates = bucket.pop("_rates")
        bucket["avgCompletion"] = round(sum(rates) / len(rates)) if rates else 0

    return stats


def serialize_teacher(teacher: Teacher, stats: dict | None = None) -> dict:
    s = stats or {
        "courseCount": 0,
        "studentCount": 0,
        "avgCompletion": 0,
        "courses": [],
        "courseIds": [],
    }
    return {
        "id": teacher.id,
        "name": teacher.name,
        "avatar": teacher.avatar or "",
        "phone": teacher.phone or "",
        "email": teacher.email or "",
        "title": teacher.title or "讲师",
        "status": int(teacher.status),
        "courseCount": s["courseCount"],
        "studentCount": s["studentCount"],
        "avgCompletion": s["avgCompletion"],
        "courses": s["courses"],
        "courseIds": s["courseIds"],
    }


def get_teacher_by_id(db: Session, teacher_id: int) -> dict | None:
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        return None
    stats = _course_stats_by_teacher(db, [teacher.id]).get(teacher.id)
    return serialize_teacher(teacher, stats)


def list_teachers_page(
    db: Session,
    *,
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    page, page_size = normalize_page(page, page_size)

    filters = []
    if name:
        filters.append(Teacher.name.contains(name))
    if status is not None and status != "":
        filters.append(Teacher.status == int(status))

    count_stmt = select(func.count(Teacher.id))
    list_stmt = select(Teacher)
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)

    total = int(db.scalar(count_stmt) or 0)
    rows = list(
        db.scalars(
            list_stmt.order_by(Teacher.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    ids = [t.id for t in rows]
    stats_map = _course_stats_by_teacher(db, ids)
    items = [serialize_teacher(t, stats_map.get(t.id)) for t in rows]
    return page_payload(items, total, page, page_size)
