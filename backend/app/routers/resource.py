from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.response import fail, ok
from app.data.store import COURSES, RESOURCES, next_resource_id, paginate
from app.deps import get_current_user, require_roles

router = APIRouter(prefix="/resource", tags=["resource"])


EXT_MAP = {
    "pdf": "PDF",
    "ppt": "PPT",
    "pptx": "PPT",
    "doc": "Word",
    "docx": "Word",
    "xls": "Excel",
    "xlsx": "Excel",
    "png": "图片",
    "jpg": "图片",
    "jpeg": "图片",
    "mp4": "视频",
    "mov": "视频",
}


def ext_type(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return EXT_MAP.get(ext, "其他")


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size / 1024 / 1024:.1f}MB"


@router.get("/list")
def list_resources(
    name: str | None = None,
    type: str | None = None,
    courseId: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(get_current_user),
):
    _ = user
    items = list(RESOURCES)
    if name:
        items = [r for r in items if name in r.get("name", "")]
    if type:
        items = [r for r in items if r.get("type") == type]
    if courseId:
        items = [r for r in items if str(r.get("courseId")) == str(courseId)]
    return ok(paginate(items, page, pageSize))


@router.post("/upload")
async def upload_resource(
    file: UploadFile = File(...),
    courseId: int = Form(...),
    user: dict = Depends(get_current_user),
):
    course = next((c for c in COURSES if c["id"] == courseId), None)
    content = await file.read()
    item = {
        "id": next_resource_id(),
        "name": file.filename or f"resource-{next_resource_id()}",
        "type": ext_type(file.filename or ""),
        "courseId": courseId,
        "courseName": course["name"] if course else "未分配课程",
        "size": format_size(len(content)),
        "uploader": user.get("nickname") or user.get("username") or "当前用户",
        "uploadedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": 1,
    }
    RESOURCES.insert(0, item)
    return ok(item)


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    user: dict = Depends(require_roles("admin")),
):
    _ = user
    index = next((i for i, r in enumerate(RESOURCES) if r["id"] == resource_id), -1)
    if index < 0:
        return fail("资源不存在", status_code=404)
    RESOURCES.pop(index)
    return ok(True)
