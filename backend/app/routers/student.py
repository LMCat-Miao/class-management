from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.response import fail, ok
from app.data.store import STUDENTS, next_student_id, paginate
from app.deps import get_current_user

router = APIRouter(prefix="/student", tags=["student"])


class StudentBody(BaseModel):
    name: str
    avatar: str | None = ""
    studentNo: str | None = None
    className: str | None = ""
    phone: str | None = ""
    status: int | None = 1


class StatusBody(BaseModel):
    status: int


@router.get("/list")
def list_students(
    name: str | None = None,
    studentNo: str | None = None,
    className: str | None = None,
    status: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(get_current_user),
):
    _ = user
    items = list(STUDENTS)
    if name:
        items = [s for s in items if name in s.get("name", "")]
    if studentNo:
        items = [s for s in items if studentNo in s.get("studentNo", "")]
    if className:
        items = [s for s in items if className in s.get("className", "")]
    if status is not None and status != "":
        items = [s for s in items if str(s.get("status")) == str(status)]
    return ok(paginate(items, page, pageSize))


@router.get("/{student_id}")
def student_detail(student_id: int, user: dict = Depends(get_current_user)):
    _ = user
    student = next((s for s in STUDENTS if s["id"] == student_id), None)
    if not student:
        return fail("学生不存在", status_code=404)
    return ok(student)


@router.post("")
def create_student(body: StudentBody, user: dict = Depends(get_current_user)):
    _ = user
    new_id = next_student_id()
    item = {
        "id": new_id,
        "name": body.name,
        "avatar": body.avatar or "",
        "studentNo": body.studentNo or f"S{new_id}",
        "className": body.className or "",
        "phone": body.phone or "",
        "learnCourseCount": 0,
        "finishCourseCount": 0,
        "progress": 0,
        "status": body.status if body.status is not None else 1,
        "registeredAt": date.today().isoformat(),
        "recentCourses": [],
        "avgCompletion": 0,
    }
    STUDENTS.insert(0, item)
    return ok(item)


@router.put("/{student_id}")
def update_student(
    student_id: int,
    body: StudentBody,
    user: dict = Depends(get_current_user),
):
    _ = user
    index = next((i for i, s in enumerate(STUDENTS) if s["id"] == student_id), -1)
    if index < 0:
        return fail("学生不存在", status_code=404)
    STUDENTS[index] = {
        **STUDENTS[index],
        **body.model_dump(exclude_unset=True),
        "id": student_id,
    }
    return ok(STUDENTS[index])


@router.put("/{student_id}/status")
def update_status(
    student_id: int,
    body: StatusBody,
    user: dict = Depends(get_current_user),
):
    _ = user
    student = next((s for s in STUDENTS if s["id"] == student_id), None)
    if not student:
        return fail("学生不存在", status_code=404)
    student["status"] = int(body.status)
    return ok(student)
