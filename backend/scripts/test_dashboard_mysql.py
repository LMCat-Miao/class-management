"""
4.3.2.2 Dashboard MySQL 统计冒烟测试。

用法：

    python scripts\\test_dashboard_mysql.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.course_category import CourseCategory
    from app.models.student import Student
    from app.models.teacher import Teacher

    client = TestClient(app)
    created_id: int | None = None
    marker = f"__TEST_DASH_{uuid.uuid4().hex[:8]}__"

    def cleanup() -> None:
        if created_id is None:
            return
        db = SessionLocal()
        try:
            row = db.get(Course, created_id)
            if row:
                db.delete(row)
                db.commit()
                print(f"[cleanup] deleted course id={created_id}")
        finally:
            db.close()

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("admin login", admin.get("code") == 0)
        admin_h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        r = client.get("/dashboard")
        check("no token 401", r.status_code == 401)

        r = client.get("/dashboard", headers=admin_h)
        body = r.json()
        check("dashboard 200", r.status_code == 200 and body.get("code") == 0)
        data = body["data"]
        for key in (
            "cards",
            "courseTrend",
            "studentTrend",
            "categoryPie",
            "hotCourses",
            "completionRate",
        ):
            check(f"field {key}", key in data)

        db = SessionLocal()
        try:
            course_total = int(db.scalar(select(func.count(Course.id))) or 0)
            teacher_total = int(db.scalar(select(func.count(Teacher.id))) or 0)
            student_total = int(db.scalar(select(func.count(Student.id))) or 0)
            learn_total = int(
                db.scalar(select(func.coalesce(func.sum(Course.learn_count), 0))) or 0
            )
            avg_raw = db.scalar(select(func.avg(Course.completion_rate)))
            completion = round(float(avg_raw)) if avg_raw is not None else 0

            cat_rows = db.execute(
                select(CourseCategory.name, func.count(Course.id))
                .join(Course, Course.category_id == CourseCategory.id)
                .group_by(CourseCategory.id, CourseCategory.name)
            ).all()
            cat_map = {n: int(c) for n, c in cat_rows}

            hot = db.scalars(
                select(Course).order_by(Course.learn_count.desc(), Course.id.asc()).limit(5)
            ).all()
            hot_names = [c.name for c in hot]
        finally:
            db.close()

        cards = data["cards"]
        check("courseTotal match", cards["courseTotal"] == course_total, str(cards["courseTotal"]))
        check("teacherTotal match", cards["teacherTotal"] == teacher_total)
        check("learnTotal match", cards["learnTotal"] == learn_total)
        check(
            "studentTotal COUNT(students)",
            cards["studentTotal"] == student_total,
            str(cards["studentTotal"]),
        )
        check("completionRate match", data["completionRate"] == completion)

        pie_map = {x["name"]: x["value"] for x in data["categoryPie"]}
        check("categoryPie match", pie_map == cat_map, f"{pie_map} vs {cat_map}")

        api_hot = [x["name"] for x in data["hotCourses"]]
        check("hotCourses order", api_hot == hot_names, f"{api_hot} vs {hot_names}")

        check("courseTrend len 12", len(data["courseTrend"]["values"]) == 12)
        check(
            "courseTrend last = total+120",
            data["courseTrend"]["values"][-1] == course_total + 120,
        )
        check("studentTrend hardcoded last", data["studentTrend"]["values"][-1] == 1100)

        # create a disposable course and ensure totals bump (then cleanup)
        r = client.post(
            "/course",
            headers=admin_h,
            json={
                "name": marker,
                "category": "前端",
                "teacherId": 1,
                "duration": 1,
                "status": 1,
            },
        )
        check("create probe course", r.json().get("code") == 0)
        created_id = r.json()["data"]["id"]

        r = client.get("/dashboard", headers=admin_h)
        check(
            "courseTotal after create",
            r.json()["data"]["cards"]["courseTotal"] == course_total + 1,
        )

        print("[dashboard-mysql] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
