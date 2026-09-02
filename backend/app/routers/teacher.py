from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.response import fail, ok
from app.data.store import COURSES, TEACHERS, next_teacher_id, paginate
from app.deps import require_roles

router = APIRouter(prefix="/teacher", tags=["teacher"])


class TeacherBody(BaseModel):
    name: str
    avatar: str | None = ""
    phone: str | None = ""
    email: str | None = ""
    title: str | None = "讲师"
    status: int | None = 1


def enrich_teacher(teacher: dict) -> dict:
    related = [c for c in COURSES if c.get("teacherId") == teacher["id"]]
    avg = (
        round(sum(c["completionRate"] for c in related) / len(related))
        if related
        else teacher.get("avgCompletion", 0)
    )
    return {
        **teacher,
        "courseCount": len(related),
        "courses": [
            {
                "id": c["id"],
                "name": c["name"],
                "studentCount": c["studentCount"],
                "completionRate": c["completionRate"],
            }
            for c in related
        ],
        "studentCount": sum(c["studentCount"] for c in related)
        or teacher.get("studentCount", 0),
        "avgCompletion": avg,
    }


@router.get("/list")
def list_teachers(
    name: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    items = [enrich_teacher(t) for t in TEACHERS]
    if name:
        items = [t for t in items if name in t.get("name", "")]
    if status is not None and status != "":
        items = [t for t in items if str(t.get("status")) == str(status)]
    return ok(paginate(items, page, pageSize))


@router.get("/{teacher_id}")
def teacher_detail(teacher_id: int, user: dict = Depends(require_roles("admin"))):
    _ = user
    teacher = next((t for t in TEACHERS if t["id"] == teacher_id), None)
    if not teacher:
        return fail("教师不存在", status_code=404)
    return ok(enrich_teacher(teacher))


@router.post("")
def create_teacher(body: TeacherBody, user: dict = Depends(require_roles("admin"))):
    _ = user
    item = {
        "id": next_teacher_id(),
        "name": body.name,
        "avatar": body.avatar or "",
        "phone": body.phone or "",
        "email": body.email or "",
        "title": body.title or "讲师",
        "courseCount": 0,
        "studentCount": 0,
        "avgCompletion": 0,
        "status": body.status if body.status is not None else 1,
        "courseIds": [],
    }
    TEACHERS.insert(0, item)
    return ok(enrich_teacher(item))


@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int,
    body: TeacherBody,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    index = next((i for i, t in enumerate(TEACHERS) if t["id"] == teacher_id), -1)
    if index < 0:
        return fail("教师不存在", status_code=404)
    TEACHERS[index] = {
        **TEACHERS[index],
        **body.model_dump(exclude_unset=True),
        "id": teacher_id,
    }
    return ok(enrich_teacher(TEACHERS[index]))


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, user: dict = Depends(require_roles("admin"))):
    _ = user
    index = next((i for i, t in enumerate(TEACHERS) if t["id"] == teacher_id), -1)
    if index < 0:
        return fail("教师不存在", status_code=404)
    TEACHERS.pop(index)
    return ok(True)
