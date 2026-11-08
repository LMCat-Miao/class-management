"""
课程只读查询：从 MySQL 读取列表与详情，序列化为原 API 字段。

4.3.1.2：列表对 teacher 强制要求有效 teacherId（teachers.id），缺失则拒绝，禁止回落为全量。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.course import Course
from app.models.course_category import CourseCategory
from app.models.teacher import Teacher


class CourseQueryError(Exception):
    """课程查询业务错误（由 Router 转为统一 fail 响应）。"""

    def __init__(self, message: str, status_code: int = 403, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def parse_list_teacher_id(raw: object) -> int | None:
    """
    解析列表用 teacherId（须为有效正整数）。

    None / 缺失 / 空串 / 非数字 / <=0 → None（调用方应拒绝，不得当作「不过滤」）。
    """
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def resolve_list_owner_teacher_id(user: dict) -> int | None:
    """
    列表数据范围：

    - admin → None（不加归属过滤）
    - teacher → 有效 teachers.id；无效则 403
    - 其他角色 → 403
    """
    role = user.get("role")
    if role == "admin":
        return None
    if role == "teacher":
        tid = parse_list_teacher_id(user.get("teacherId"))
        if tid is None:
            raise CourseQueryError("无权限访问", status_code=403)
        return tid
    raise CourseQueryError("无权限访问", status_code=403)


def serialize_course(course: Course) -> dict:
    """
    ORM → 前端契约字段。

    - category_id → category（中文名）
    - teacher_id → teacherId + teacher（姓名）
    - chapters_json → chapters
    - created_at(DATE) → createdAt「YYYY-MM-DD」
    """
    category_name = course.category.name if course.category else ""
    teacher_name = course.teacher.name if course.teacher else ""
    created = course.created_at
    if isinstance(created, datetime):
        created_at = created.date().isoformat()
    elif isinstance(created, date):
        created_at = created.isoformat()
    else:
        created_at = str(created) if created else ""

    chapters = course.chapters_json if isinstance(course.chapters_json, list) else []

    return {
        "id": course.id,
        "name": course.name,
        "cover": course.cover or "",
        "category": category_name,
        "teacherId": course.teacher_id,
        "teacher": teacher_name,
        "difficulty": course.difficulty,
        "duration": course.duration,
        "studentCount": course.student_count,
        "learnCount": course.learn_count,
        "completionRate": course.completion_rate,
        "status": course.status,
        "intro": course.intro or "",
        "createdAt": created_at,
        "chapters": chapters,
    }


def _base_list_stmt() -> Select[tuple[Course]]:
    """列表查询基础语句：关联分类与教师，便于按名称筛选。"""
    return (
        select(Course)
        .join(Course.category)
        .join(Course.teacher)
        .options(
            joinedload(Course.category),
            joinedload(Course.teacher),
        )
    )


def _apply_list_filters(
    stmt: Select[tuple[Course]],
    *,
    owner_teacher_id: int | None,
    name: str | None,
    category: str | None,
    teacher: str | None,
    status: str | None,
    start_date: str | None,
    end_date: str | None,
) -> Select[tuple[Course]]:
    # owner_teacher_id 为 teachers.id；None 表示 admin 不加归属限制
    if owner_teacher_id is not None:
        stmt = stmt.where(Course.teacher_id == int(owner_teacher_id))

    if name:
        stmt = stmt.where(Course.name.contains(name))
    if category:
        stmt = stmt.where(CourseCategory.name == category)
    if teacher:
        stmt = stmt.where(Teacher.name.contains(teacher))
    if status is not None and status != "":
        stmt = stmt.where(Course.status == int(status))
    if start_date:
        stmt = stmt.where(Course.created_at >= date.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(Course.created_at <= date.fromisoformat(end_date))
    return stmt


def list_courses_page(
    db: Session,
    *,
    user: dict,
    name: str | None = None,
    category: str | None = None,
    teacher: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """
    分页列表，形状与原 paginate 一致：
    { list, total, page, pageSize }

    教师无有效 teacherId 时抛 CourseQueryError(403)，绝不返回全量课程。
    """
    owner_teacher_id = resolve_list_owner_teacher_id(user)

    page = max(int(page or 1), 1)
    page_size = max(int(page_size or 10), 1)

    stmt = _apply_list_filters(
        _base_list_stmt(),
        owner_teacher_id=owner_teacher_id,
        name=name,
        category=category,
        teacher=teacher,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )

    # 总数：同一套过滤条件（不带 joinedload，避免重复计数问题）
    count_stmt = _apply_list_filters(
        select(func.count(Course.id)).join(Course.category).join(Course.teacher),
        owner_teacher_id=owner_teacher_id,
        name=name,
        category=category,
        teacher=teacher,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )
    total = int(db.scalar(count_stmt) or 0)

    rows = db.scalars(
        stmt.order_by(Course.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()

    return {
        "list": [serialize_course(row) for row in rows],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }


def get_course_by_id(db: Session, course_id: int) -> dict | None:
    """详情主体（不含 resources）；不存在返回 None。"""
    course = db.scalar(
        select(Course)
        .where(Course.id == course_id)
        .options(
            joinedload(Course.category),
            joinedload(Course.teacher),
        )
    )
    if not course:
        return None
    return serialize_course(course)


def can_view_course(user: dict, course: dict) -> bool:
    """
    课程详情归属校验（与列表规则对齐）。

    - admin：可看全部
    - teacher：仅当 course.teacherId == user.teacherId（均为 teachers.id）
    - 教师无 teacherId：不能查看任何课程详情
    """
    if user.get("role") == "admin":
        return True
    if user.get("role") == "teacher":
        tid = user.get("teacherId")
        if tid is None:
            return False
        return int(course.get("teacherId")) == int(tid)
    return False

