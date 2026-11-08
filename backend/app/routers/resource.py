"""
课程资源（4.3.3.4）：MySQL resources + 真实文件落盘。
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.deps import get_current_user, require_roles
from app.services.resource_access import ResourceAccessError
from app.services.resource_query import list_resources_page
from app.services.resource_write import (
    ResourceWriteError,
    delete_resource,
    resolve_download_path,
    upload_resource,
)

router = APIRouter(prefix="/resource", tags=["resource"])


@router.get("/list")
def list_resources(
    name: str | None = None,
    type: str | None = None,
    courseId: str | None = None,
    page: int = 1,
    pageSize: int = 10,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = list_resources_page(
            db,
            user=user,
            name=name,
            type_filter=type,
            course_id_raw=courseId,
            page=page,
            page_size=pageSize,
        )
    except ResourceAccessError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(data)


@router.post("/upload")
async def upload_resource_api(
    file: UploadFile = File(...),
    courseId: int = Form(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        item = await upload_resource(db, user=user, file=file, course_id=int(courseId))
    except ResourceAccessError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    except ResourceWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(item)


@router.get("/{resource_id}/download")
def download_resource(
    resource_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        path, filename = resolve_download_path(db, user, resource_id)
    except ResourceWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)

    # RFC 5987 处理中文文件名；不向客户端暴露服务器绝对路径
    quoted = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quoted}",
    }
    return FileResponse(
        path=str(path),
        filename=filename,
        headers=headers,
        media_type="application/octet-stream",
    )


@router.delete("/{resource_id}")
def delete_resource_api(
    resource_id: int,
    user: dict = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    _ = user
    try:
        delete_resource(db, resource_id)
    except ResourceWriteError as exc:
        return fail(exc.message, code=exc.code, status_code=exc.status_code)
    return ok(True)
