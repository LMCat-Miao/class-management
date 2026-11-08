"""
将 store.RESOURCES 演示元数据幂等导入 MySQL resources（4.3.3.5）。

默认 dry-run；正式写入须加 --apply。

    python scripts\\migrate_resources_from_store.py
    python scripts\\migrate_resources_from_store.py --apply

规则：
- 幂等键：(course_id, name, uploaded_at 规范化)
- 已存在则跳过，不覆盖
- size 字符串转字节；file_path=NULL（无真实文件）
- courseId 须对应真实 courses.id，否则跳过
- 不猜测 uploader_user_id
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.data.store import RESOURCES  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.resource import Resource  # noqa: E402


_SIZE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([KMGTP]?B)\s*$", re.I)


def parse_size_to_bytes(raw: str) -> int:
    """
    将可读大小转为字节。
    例：2.4MB → int(2.4 * 1024**2)；1.2KB → int(1.2 * 1024)
    """
    m = _SIZE_RE.match(str(raw or ""))
    if not m:
        raise ValueError(f"无法解析 size: {raw!r}")
    num = float(m.group(1))
    unit = m.group(2).upper()
    mult = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
        "PB": 1024**5,
    }.get(unit)
    if mult is None:
        raise ValueError(f"未知单位: {unit}")
    return int(num * mult)


def parse_uploaded_at(raw: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析 uploadedAt: {raw!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import RESOURCES into MySQL (idempotent)")
    parser.add_argument("--apply", action="store_true", help="实际写入；默认 dry-run")
    args = parser.parse_args()

    to_import: list[dict] = []
    to_skip: list[str] = []
    failed: list[str] = []

    db = SessionLocal()
    try:
        course_ids = {int(x) for x in db.scalars(select(Course.id)).all()}
        existing = {
            (int(r.course_id), r.name, r.uploaded_at.strftime("%Y-%m-%d %H:%M") if r.uploaded_at else "")
            for r in db.scalars(select(Resource)).all()
        }

        for item in RESOURCES:
            label = f"id={item.get('id')} name={item.get('name')}"
            try:
                course_id = int(item["courseId"])
            except Exception:
                failed.append(f"{label}: invalid courseId")
                continue
            if course_id not in course_ids:
                failed.append(f"{label}: course {course_id} not found")
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                failed.append(f"{label}: empty name")
                continue
            try:
                uploaded_at = parse_uploaded_at(str(item["uploadedAt"]))
                size_bytes = parse_size_to_bytes(str(item.get("size") or "0B"))
            except Exception as exc:
                failed.append(f"{label}: {exc}")
                continue

            key = (course_id, name, uploaded_at.strftime("%Y-%m-%d %H:%M"))
            if key in existing:
                to_skip.append(f"{name}@{course_id}")
                continue

            to_import.append(
                {
                    "course_id": course_id,
                    "name": name,
                    "type": str(item.get("type") or "其他"),
                    "size": size_bytes,
                    "uploader": str(item.get("uploader") or "")[:64],
                    "uploader_user_id": None,
                    "uploaded_at": uploaded_at,
                    "status": int(item.get("status") if item.get("status") is not None else 1),
                    "file_path": None,
                }
            )

        print(f"[plan] import={len(to_import)} skip={len(to_skip)} fail={len(failed)}")
        if to_skip:
            print("  skip:", ", ".join(to_skip))
        if failed:
            print("  fail:", "; ".join(failed))
        if to_import:
            print("  will import:", ", ".join(m["name"] for m in to_import))

        if not args.apply:
            print("[dry-run] 未写入。加 --apply 执行导入。")
            return 0

        for mapped in to_import:
            db.add(Resource(**mapped))
        db.commit()
        print(f"[done] imported={len(to_import)} skipped={len(to_skip)} failed={len(failed)}")
        return 0 if not failed else 1
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] {exc}")
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
