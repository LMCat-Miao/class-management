from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.response import fail, ok
from app.data.store import COURSES, RESOURCES, TEACHERS, next_course_id, paginate
from app.deps import get_current_user, require_roles

router = APIRouter(prefix="/course", tags=["course"])


class CourseBody(BaseModel):
    name: str
    cover: str | None = None
    category: str | None = None
    teacherId: int | None = None
    teacher: str | None = None
    difficulty: str | None = "初级"
    duration: int | None = 0
    status: int | None = 1
    intro: str | None = ""
    chapters: list[dict[str, Any]] | None = None


class StatusBody(BaseModel):
    status: int


def enrich_course(course: dict) -> dict:
    teacher = next((t for t in TEACHERS if t["id"] == course.get("teacherId")), None)
    return {**course, "teacher": teacher["name"] if teacher else course.get("teacher", "")}


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
):
    items = [enrich_course(c) for c in COURSES]

    # 教师只看自己的课
    if user.get("role") == "teacher" and user.get("teacherId"):
        items = [c for c in items if c.get("teacherId") == user["teacherId"]]

    if name:
        items = [c for c in items if name in c.get("name", "")]
    if category:
        items = [c for c in items if c.get("category") == category]
    if teacher:
        items = [c for c in items if teacher in c.get("teacher", "")]
    if status is not None and status != "":
        items = [c for c in items if str(c.get("status")) == str(status)]
    if startDate:
        items = [c for c in items if c.get("createdAt", "") >= startDate]
    if endDate:
        items = [c for c in items if c.get("createdAt", "") <= endDate]

    return ok(paginate(items, page, pageSize))


@router.get("/{course_id}")
def course_detail(course_id: int, user: dict = Depends(get_current_user)):
    _ = user
    course = next((c for c in COURSES if c["id"] == course_id), None)
    if not course:
        return fail("课程不存在", status_code=404)
    related = [r for r in RESOURCES if r.get("courseId") == course_id]
    return ok({**enrich_course(course), "resources": related})


@router.post("")
def create_course(
    body: CourseBody,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    teacher = next((t for t in TEACHERS if t["id"] == body.teacherId), None)
    item = {
        "id": next_course_id(),
        "name": body.name,
        "cover": body.cover or "https://picsum.photos/seed/newcourse/160/90",
        "category": body.category or "前端",
        "teacherId": body.teacherId or (teacher["id"] if teacher else 1),
        "teacher": teacher["name"] if teacher else (body.teacher or ""),
        "difficulty": body.difficulty or "初级",
        "duration": body.duration or 0,
        "studentCount": 0,
        "learnCount": 0,
        "completionRate": 0,
        "status": body.status if body.status is not None else 1,
        "intro": body.intro or "",
        "createdAt": date.today().isoformat(),
        "chapters": body.chapters or [{"id": 1, "title": "第一章 课程导论"}],
    }
    COURSES.insert(0, item)
    return ok(enrich_course(item))


@router.put("/{course_id}")
def update_course(
    course_id: int,
    body: CourseBody,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    index = next((i for i, c in enumerate(COURSES) if c["id"] == course_id), -1)
    if index < 0:
        return fail("课程不存在", status_code=404)
    teacher = next((t for t in TEACHERS if t["id"] == body.teacherId), None)
    payload = body.model_dump(exclude_unset=True)
    COURSES[index] = {
        **COURSES[index],
        **payload,
        "id": course_id,
        "teacherId": body.teacherId or COURSES[index]["teacherId"],
        "teacher": teacher["name"]
        if teacher
        else payload.get("teacher", COURSES[index].get("teacher")),
    }
    return ok(enrich_course(COURSES[index]))


@router.delete("/{course_id}")
def delete_course(course_id: int, user: dict = Depends(require_roles("admin"))):
    _ = user
    index = next((i for i, c in enumerate(COURSES) if c["id"] == course_id), -1)
    if index < 0:
        return fail("课程不存在", status_code=404)
    COURSES.pop(index)
    return ok(True)


@router.put("/{course_id}/status")
def update_status(
    course_id: int,
    body: StatusBody,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    course = next((c for c in COURSES if c["id"] == course_id), None)
    if not course:
        return fail("课程不存在", status_code=404)
    course["status"] = int(body.status)
    return ok(enrich_course(course))
