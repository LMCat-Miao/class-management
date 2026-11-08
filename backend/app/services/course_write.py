"""
课程写入服务：

- 4.2.1：create_course → MySQL
- 4.2.2：update_course → MySQL
- 4.2.3 / 4.3.3.4：delete_course → MySQL（先删资源元数据再删课程，commit 后清文件）
- 4.2.4：update_course_status → MySQL
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_category import CourseCategory
from app.models.teacher import Teacher
from app.services.course_query import get_course_by_id
from app.services.resource_write import ResourceWriteError, delete_course_with_resources

DEFAULT_COVER = "https://picsum.photos/seed/newcourse/160/90"
DEFAULT_CHAPTERS = [{"id": 1, "title": "第一章 课程导论"}]


class CourseWriteError(Exception):
    """课程写入业务错误（由 Router 转为统一 fail 响应）。"""

    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


ALLOWED_COURSE_STATUS = frozenset({0, 1})


def normalize_course_status(raw: Any) -> int:
    """
    将输入规范为合法上下架状态（仅 0 / 1）。

    - 拒绝 bool（True/False 是 int 子类，不能当作 1/0）
    - 拒绝无法转为 int 或转后不在 {0,1} 的值
    """
    if isinstance(raw, bool):
        raise CourseWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise CourseWriteError("状态值无效，仅允许 0 或 1", status_code=400) from exc
    # 拒绝 1.5 等被 int() 截断后“碰巧”合法的浮点
    if isinstance(raw, float) and float(raw) != float(value):
        raise CourseWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    if value not in ALLOWED_COURSE_STATUS:
        raise CourseWriteError("状态值无效，仅允许 0 或 1", status_code=400)
    return value


def create_course(db: Session, data: Any) -> dict:
    """
    新增课程并写入 MySQL。

    data：具备 CourseBody 属性的对象（或等价命名空间），字段与 API 一致。
    返回：与列表/详情相同的序列化 dict（含中文 category、教师姓名等）。
    """
    name = (getattr(data, "name", None) or "").strip()
    if not name:
        raise CourseWriteError("请输入课程名称", status_code=400)

    category_name = getattr(data, "category", None) or "前端"
    category_name = str(category_name).strip()
    category = db.scalar(
        select(CourseCategory).where(CourseCategory.name == category_name)
    )
    if not category:
        raise CourseWriteError(f"课程分类不存在：{category_name}", status_code=400)

    teacher_id = getattr(data, "teacherId", None)
    if teacher_id is None:
        raise CourseWriteError("请选择授课教师", status_code=400)
    teacher = db.get(Teacher, int(teacher_id))
    if not teacher:
        raise CourseWriteError("授课教师不存在", status_code=400)

    cover = getattr(data, "cover", None)
    cover = cover if cover not in (None, "") else DEFAULT_COVER

    difficulty = getattr(data, "difficulty", None) or "初级"

    # 注意：不能用 `duration or 0`，否则合法的 0 会被误判
    raw_duration = getattr(data, "duration", None)
    duration = 0 if raw_duration is None else int(raw_duration)

    # 未传 / None：保持原默认上架 1；显式传入则走统一 0/1 校验（拒 bool）
    raw_status = getattr(data, "status", None)
    status = 1 if raw_status is None else normalize_course_status(raw_status)

    intro = getattr(data, "intro", None)
    intro = "" if intro is None else str(intro)

    raw_chapters = getattr(data, "chapters", None)
    # 与旧 API 一致：None / 空列表时使用默认导论章
    chapters = list(raw_chapters) if raw_chapters else list(DEFAULT_CHAPTERS)

    completion_rate = 0
    if completion_rate < 0 or completion_rate > 100:
        raise CourseWriteError("完成率必须在 0～100 之间", status_code=400)

    course = Course(
        name=name,
        cover=cover,
        category_id=category.id,
        teacher_id=teacher.id,
        difficulty=difficulty,
        duration=duration,
        student_count=0,
        learn_count=0,
        completion_rate=completion_rate,
        status=status,
        intro=intro,
        chapters_json=chapters,
        created_at=date.today(),
    )

    try:
        db.add(course)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise CourseWriteError("课程创建失败", status_code=500) from exc

    # 用只读序列化路径返回，保证与 list/detail 字段一致
    created = get_course_by_id(db, course.id)
    if not created:
        raise CourseWriteError("课程创建后读取失败", status_code=500)
    return created


def update_course(db: Session, course_id: int, update_data: dict[str, Any]) -> dict:
    """
    按字段部分更新课程（仅 update_data 中出现的键）。

    - 未传 chapters：不改 chapters_json
    - category：中文名 → category_id（不存在则 400）
    - teacherId：teachers.id（不存在则 400；禁止默认 1）
    - duration：允许 0，用 is None 判断，不用 `or`
    - status：仅当键出现且非 None 时更新；只允许 0/1（与上下架接口一致）
    """
    course = db.get(Course, course_id)
    if not course:
        raise CourseWriteError("课程不存在", status_code=404)

    # 忽略仅用于响应展示、不落库的键
    data = {k: v for k, v in update_data.items() if k != "teacher"}

    if "name" in data:
        name = (data["name"] or "").strip() if data["name"] is not None else ""
        if not name:
            raise CourseWriteError("请输入课程名称", status_code=400)
        course.name = name

    if "cover" in data:
        course.cover = "" if data["cover"] is None else str(data["cover"])

    if "category" in data:
        category_name = data["category"]
        if category_name is None or str(category_name).strip() == "":
            raise CourseWriteError("请选择课程分类", status_code=400)
        category_name = str(category_name).strip()
        category = db.scalar(
            select(CourseCategory).where(CourseCategory.name == category_name)
        )
        if not category:
            raise CourseWriteError(f"课程分类不存在：{category_name}", status_code=400)
        course.category_id = category.id

    if "teacherId" in data:
        teacher_id = data["teacherId"]
        if teacher_id is None:
            raise CourseWriteError("请选择授课教师", status_code=400)
        teacher = db.get(Teacher, int(teacher_id))
        if not teacher:
            raise CourseWriteError("授课教师不存在", status_code=400)
        course.teacher_id = teacher.id

    if "difficulty" in data and data["difficulty"] is not None:
        course.difficulty = str(data["difficulty"])

    if "duration" in data:
        # 合法 0 必须保留
        course.duration = 0 if data["duration"] is None else int(data["duration"])

    if "status" in data and data["status"] is not None:
        # 未传 status 不进入本分支，保持库中原值；禁止 bool / 越界值
        course.status = normalize_course_status(data["status"])

    if "intro" in data:
        course.intro = "" if data["intro"] is None else str(data["intro"])

    if "chapters" in data:
        # 仅当请求明确带了 chapters 才更新；空列表也允许写入
        raw = data["chapters"]
        course.chapters_json = list(raw) if raw is not None else []

    try:
        db.add(course)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise CourseWriteError("课程更新失败", status_code=500) from exc

    updated = get_course_by_id(db, course.id)
    if not updated:
        raise CourseWriteError("课程更新后读取失败", status_code=500)
    return updated


def delete_course(db: Session, course_id: int) -> bool:
    """
    删除课程：存在选课关系则 409；否则事务内删 resources + course，commit 后清磁盘文件。
    """
    try:
        return delete_course_with_resources(db, course_id)
    except ResourceWriteError as exc:
        raise CourseWriteError(exc.message, status_code=exc.status_code, code=exc.code) from exc


def update_course_status(db: Session, course_id: int, status: int) -> dict:
    """
    上下架：仅更新 MySQL courses.status。

    - 仅允许 0（下架）/ 1（上架）；0 为合法值，不得用 `status or ...` 吞掉。
    - 成功后返回与详情一致的序列化 dict（对齐原 Router ok(enrich_course(...))）。
    """
    status_value = normalize_course_status(status)

    course = db.get(Course, course_id)
    if not course:
        raise CourseWriteError("课程不存在", status_code=404)

    course.status = status_value

    try:
        db.add(course)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise CourseWriteError("课程状态更新失败", status_code=500) from exc

    updated = get_course_by_id(db, course.id)
    if not updated:
        raise CourseWriteError("课程状态更新后读取失败", status_code=500)
    return updated
