"""
课程资源访问控制（4.3.1.1 / 4.3.3.4 复用）。

课程是否存在与归属一律以 MySQL Course 为准。
teacherId 必须为 teachers.id，禁止用 users.id 代替。
列表/上传/下载的资源元数据由 resource_query / resource_write 读 MySQL。
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course


class ResourceAccessError(Exception):
    """资源权限 / 课程校验错误（由 Router 转为 fail 响应）。"""

    def __init__(self, message: str, status_code: int = 403, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def parse_course_id(raw: str | int | None) -> int | None:
    """解析 courseId；空视为未传；非法格式 → 400。"""
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ResourceAccessError("课程 ID 无效", status_code=400) from exc


def get_course_for_resource(db: Session, course_id: int) -> Course:
    """按 MySQL 取课程；不存在 → 404。"""
    course = db.get(Course, course_id)
    if not course:
        raise ResourceAccessError("课程不存在", status_code=404)
    return course


def assert_can_manage_course_resources(user: dict, course: Course) -> None:
    """
    校验当前用户能否访问/上传该课程资源。

    - admin：任意存在课程
    - teacher：须有 teacherId，且 course.teacher_id == teacherId
    - 其他角色：403
    """
    role = user.get("role")
    if role == "admin":
        return

    if role == "teacher":
        tid = user.get("teacherId")
        if tid is None:
            raise ResourceAccessError("无权限访问", status_code=403)
        if int(course.teacher_id) != int(tid):
            raise ResourceAccessError("无权限访问", status_code=403)
        return

    raise ResourceAccessError("无权限访问", status_code=403)


def resolve_course_for_write(db: Session, user: dict, course_id: int) -> Course:
    """上传前：课程存在 + 归属校验。"""
    course = get_course_for_resource(db, course_id)
    assert_can_manage_course_resources(user, course)
    return course


def teacher_owned_course_ids(db: Session, teacher_id: int) -> set[int]:
    """当前教师名下全部课程 id（teachers.id）。"""
    rows = db.scalars(
        select(Course.id).where(Course.teacher_id == int(teacher_id))
    ).all()
    return {int(x) for x in rows}


def filter_resources_for_list(
    db: Session,
    user: dict,
    resources: list[dict],
    *,
    course_id_raw: str | None,
) -> list[dict]:
    """
    列表 ACL + 按 courseId 过滤。

    admin：未传 courseId → 全部；传了 → 课程须存在，再按 courseId 过滤。
    teacher：无 teacherId → 403；未传 → 仅本人课程资源；传了 → 存在且归属后过滤。
    """
    role = user.get("role")
    course_id = parse_course_id(course_id_raw)

    if role == "admin":
        if course_id is not None:
            get_course_for_resource(db, course_id)
            return [r for r in resources if str(r.get("courseId")) == str(course_id)]
        return list(resources)

    if role == "teacher":
        tid = user.get("teacherId")
        if tid is None:
            raise ResourceAccessError("无权限访问", status_code=403)

        if course_id is not None:
            course = get_course_for_resource(db, course_id)
            assert_can_manage_course_resources(user, course)
            return [r for r in resources if str(r.get("courseId")) == str(course_id)]

        allowed = teacher_owned_course_ids(db, int(tid))
        return [
            r
            for r in resources
            if _resource_course_id(r) in allowed
        ]

    raise ResourceAccessError("无权限访问", status_code=403)


def _resource_course_id(resource: dict) -> int | None:
    raw = resource.get("courseId")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def cleanup_upload_file(path: Path | None) -> None:
    """删除本次上传产生的文件；path 为空则忽略。不触碰其他文件。"""
    if path is None:
        return
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
