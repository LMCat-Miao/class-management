"""
将 store.STUDENTS 演示数据幂等导入 MySQL students（4.3.3.5）。

默认 dry-run；正式写入须加 --apply。

    python scripts\\migrate_students_from_store.py
    python scripts\\migrate_students_from_store.py --apply

规则：
- 按 student_no 判断是否已存在；已存在则跳过（不覆盖）
- recentCourses 写入 recent_courses_json 展示快照，不创建 enrollments
- 不修改 users / teachers / courses
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.data.store import STUDENTS  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.student import Student  # noqa: E402


def _parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import STUDENTS into MySQL (idempotent)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际写入数据库；默认仅 dry-run",
    )
    args = parser.parse_args()

    to_import: list[dict] = []
    to_skip: list[str] = []
    failed: list[str] = []

    db = SessionLocal()
    try:
        existing_nos = {
            r for r in db.scalars(select(Student.student_no)).all()
        }

        for item in STUDENTS:
            sno = str(item.get("studentNo") or "").strip()
            if not sno:
                failed.append(f"id={item.get('id')}: missing studentNo")
                continue
            if sno in existing_nos:
                to_skip.append(sno)
                continue
            try:
                mapped = {
                    "student_no": sno,
                    "name": str(item.get("name") or "").strip(),
                    "avatar": item.get("avatar") or "",
                    "class_name": item.get("className") or "",
                    "phone": item.get("phone") or "",
                    "learn_course_count": int(item.get("learnCourseCount") or 0),
                    "finish_course_count": int(item.get("finishCourseCount") or 0),
                    "progress": int(item.get("progress") or 0),
                    "avg_completion": int(item.get("avgCompletion") or 0),
                    "status": int(item.get("status") if item.get("status") is not None else 1),
                    "registered_at": _parse_date(str(item["registeredAt"])),
                    "recent_courses_json": list(item.get("recentCourses") or []),
                }
            except Exception as exc:
                failed.append(f"{sno}: map error {exc}")
                continue
            if not mapped["name"]:
                failed.append(f"{sno}: empty name")
                continue
            to_import.append(mapped)

        print(f"[plan] import={len(to_import)} skip={len(to_skip)} fail={len(failed)}")
        if to_skip:
            print("  skip student_no:", ", ".join(to_skip))
        if failed:
            print("  fail:", "; ".join(failed))
        if to_import:
            print("  will import:", ", ".join(m["student_no"] for m in to_import))

        if not args.apply:
            print("[dry-run] 未写入。加 --apply 执行导入。")
            return 0

        for mapped in to_import:
            db.add(Student(**mapped))
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
