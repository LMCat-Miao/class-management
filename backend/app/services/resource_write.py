"""
资源写入与文件落盘（4.3.3.4 / 4.3.3.1 事务一致性修复）。

上传安全顺序：
1) 权限与课程归属
2) 写临时文件并校验大小/类型
3) 原子移动到正式路径
4) 写 DB 并 commit
5) DB 失败则删除刚落盘的正式文件；任一步失败清理临时文件

删除：DB commit 成功后再清磁盘；清理失败只记日志，不回滚已提交删除。
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.resource import Resource
from app.services.file_content import FileContentError, validate_upload_content
from app.services.resource_access import (
    ResourceAccessError,
    cleanup_upload_file,
    resolve_course_for_write,
)
from app.services.resource_query import serialize_resource

logger = logging.getLogger(__name__)

ALLOWED_EXT_MAP = {
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

CHUNK_SIZE = 1024 * 1024  # 1MB


class ResourceWriteError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code if code is not None else status_code


def upload_root() -> Path:
    root = Path(settings.upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def ext_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT_MAP:
        raise ResourceWriteError(
            f"不支持的文件类型，允许：{', '.join(sorted(set(ALLOWED_EXT_MAP.keys())))}",
            status_code=400,
        )
    return ALLOWED_EXT_MAP[ext]


def safe_relative_path(rel: str) -> Path:
    """确保相对路径落在 upload_root 内，防路径穿越。"""
    root = upload_root()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ResourceWriteError("非法文件路径", status_code=400) from exc
    return candidate


def _planned_relative_path(course_id: int, original_name: str) -> str:
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
    return f"courses/{int(course_id)}/{uuid.uuid4().hex}{ext}"


def atomic_move_into_place(temp_path: Path, final_rel: str) -> Path:
    """
    将临时文件原子落到正式相对路径。
    优先 os.replace（同卷原子替换）；失败则清理已创建目标并抛错。
    """
    dest = safe_relative_path(final_rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(str(temp_path), str(dest))
    except OSError as exc:
        cleanup_upload_file(dest)
        raise ResourceWriteError("资源文件落盘失败", status_code=500) from exc
    return dest


async def save_upload_to_temp(file: UploadFile, *, max_bytes: int) -> tuple[Path, int, str]:
    """分块写入临时文件，返回 (temp_path, size, original_name)。"""
    original = Path(file.filename or "resource.bin").name
    if not original or original in (".", ".."):
        original = "resource.bin"
    if "/" in (file.filename or "") or "\\" in (file.filename or ""):
        original = Path(file.filename or "resource.bin").name

    ext_type(original)

    root = upload_root()
    tmp_dir = root / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = tmp_dir / f"{uuid.uuid4().hex}.part"

    size = 0
    try:
        with temp_path.open("wb") as out:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise ResourceWriteError(
                        f"文件过大，上限 {max_bytes // (1024 * 1024)}MB",
                        status_code=400,
                    )
                out.write(chunk)
    except Exception:
        cleanup_upload_file(temp_path)
        raise

    if size == 0:
        cleanup_upload_file(temp_path)
        raise ResourceWriteError("空文件不允许上传", status_code=400)

    return temp_path, size, original


async def upload_resource(
    db: Session,
    *,
    user: dict,
    file: UploadFile,
    course_id: int,
) -> dict:
    # 1) 权限：失败时不得读大文件、不得创建文件
    course = resolve_course_for_write(db, user, int(course_id))

    max_bytes = int(settings.upload_max_bytes)
    temp_path: Path | None = None
    final_rel: str | None = None
    final_abs: Path | None = None

    try:
        # 2–3) 临时文件 + 扩展名 + 实际内容（魔术字节/结构）校验
        temp_path, size, original = await save_upload_to_temp(file, max_bytes=max_bytes)
        rtype = ext_type(original)
        try:
            validate_upload_content(temp_path, original)
        except FileContentError as exc:
            raise ResourceWriteError(exc.message, status_code=exc.status_code) from exc
        final_rel = _planned_relative_path(course.id, original)

        # 4) 原子移动到正式路径（此时尚无 DB 记录）
        final_abs = atomic_move_into_place(temp_path, final_rel)
        temp_path = None  # 已不在原临时路径

        uploader_name = user.get("nickname") or user.get("username") or "当前用户"
        uploader_uid = user.get("id")
        try:
            uploader_uid = int(uploader_uid) if uploader_uid is not None else None
        except (TypeError, ValueError):
            uploader_uid = None

        # 5) 创建 DB 记录并 commit；失败则删除刚落盘文件
        row = Resource(
            course_id=course.id,
            name=original,
            type=rtype,
            size=size,
            uploader=str(uploader_name)[:64],
            uploader_user_id=uploader_uid,
            uploaded_at=datetime.now(),
            status=1,
            file_path=final_rel,
        )
        try:
            db.add(row)
            db.commit()
            db.refresh(row)
        except SQLAlchemyError as exc:
            db.rollback()
            if final_abs is not None:
                cleanup_upload_file(final_abs)
                final_abs = None
                final_rel = None
            raise ResourceWriteError("资源上传失败", status_code=500) from exc

    except ResourceAccessError:
        cleanup_upload_file(temp_path)
        if final_abs is not None:
            cleanup_upload_file(final_abs)
        raise
    except ResourceWriteError:
        cleanup_upload_file(temp_path)
        if final_abs is not None:
            cleanup_upload_file(final_abs)
        raise
    except Exception as exc:
        cleanup_upload_file(temp_path)
        if final_abs is not None:
            cleanup_upload_file(final_abs)
        raise ResourceWriteError("资源上传失败", status_code=500) from exc

    return serialize_resource(row, course.name)


def _cleanup_disk_file(*, resource_id: int | None, rel: str, context: str) -> bool:
    """
    清理相对路径文件。返回 True 表示文件已不存在或已成功删除。
    失败只记日志（相对路径 + 原因），不抛出；不泄露服务器绝对路径。
    """
    try:
        path = safe_relative_path(rel)
    except ResourceWriteError as exc:
        logger.warning(
            "%s: invalid relative path resource_id=%s rel=%s reason=%s",
            context,
            resource_id,
            rel,
            exc.message,
        )
        return False

    if not path.is_file():
        logger.warning(
            "%s: file already missing resource_id=%s rel=%s",
            context,
            resource_id,
            rel,
        )
        return True

    try:
        path.unlink()
        return True
    except OSError as exc:
        logger.error(
            "%s: file cleanup failed resource_id=%s rel=%s reason=%s",
            context,
            resource_id,
            rel,
            exc,
        )
        return False


def delete_resource(db: Session, resource_id: int) -> bool:
    """
    admin 删除：记相对路径 → 删 DB 并 commit → 再清磁盘。
    文件缺失允许完成元数据删除；清理失败记日志，不回滚已提交删除，也不伪造「文件已删」。
    返回 True 表示数据库删除已提交成功。
    """
    row = db.get(Resource, resource_id)
    if not row:
        raise ResourceWriteError("资源不存在", status_code=404)

    rel = row.file_path
    try:
        db.delete(row)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ResourceWriteError("资源删除失败", status_code=500) from exc

    if rel:
        ok = _cleanup_disk_file(
            resource_id=resource_id, rel=rel, context="resource_delete"
        )
        if not ok:
            logger.error(
                "resource_delete: DB deleted but disk cleanup incomplete resource_id=%s rel=%s",
                resource_id,
                rel,
            )
    return True


def delete_course_with_resources(db: Session, course_id: int) -> bool:
    """
    删除课程：有选课 → 409；否则事务内删 resources + course，commit 后再逐个清文件。
    清理失败逐项记日志，不回滚已提交的数据库删除。
    """
    course = db.get(Course, course_id)
    if not course:
        raise ResourceWriteError("课程不存在", status_code=404)

    enroll_cnt = db.scalar(
        select(Enrollment.id).where(Enrollment.course_id == course_id).limit(1)
    )
    if enroll_cnt is not None:
        raise ResourceWriteError("课程存在选课关系，无法删除", status_code=409)

    resources = list(
        db.scalars(select(Resource).where(Resource.course_id == course_id)).all()
    )
    # commit 前收集 (resource_id, rel)，避免提交后无法关联 id
    pending_files = [
        (int(r.id), str(r.file_path))
        for r in resources
        if r.file_path
    ]

    try:
        for r in resources:
            db.delete(r)
        db.delete(course)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ResourceWriteError("课程删除失败", status_code=500) from exc

    failed: list[str] = []
    for rid, rel in pending_files:
        ok = _cleanup_disk_file(
            resource_id=rid, rel=rel, context="course_delete"
        )
        if not ok:
            failed.append(f"id={rid} rel={rel}")

    if failed:
        logger.error(
            "course_delete: DB deleted course_id=%s but disk cleanup failed for: %s",
            course_id,
            "; ".join(failed),
        )
    return True


def resolve_download_path(db: Session, user: dict, resource_id: int) -> tuple[Path, str]:
    """返回 (绝对路径, 原始文件名)。"""
    row = db.get(Resource, resource_id)
    if not row:
        raise ResourceWriteError("资源不存在", status_code=404)

    course = db.get(Course, row.course_id)
    if not course:
        raise ResourceWriteError("课程不存在", status_code=404)

    from app.services.resource_access import assert_can_manage_course_resources

    try:
        assert_can_manage_course_resources(user, course)
    except ResourceAccessError as exc:
        raise ResourceWriteError(exc.message, status_code=exc.status_code, code=exc.code) from exc

    if not row.file_path:
        raise ResourceWriteError("资源文件不存在（无落盘路径）", status_code=404)

    path = safe_relative_path(row.file_path)
    if not path.is_file():
        raise ResourceWriteError("资源文件缺失", status_code=404)
    return path, row.name
