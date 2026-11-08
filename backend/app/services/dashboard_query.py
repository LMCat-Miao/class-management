"""
Dashboard 统计（4.3.3.5）：课程/教师/学生总量均从 MySQL 聚合。

说明：studentTrend / courseTrend 仍为展示用硬编码趋势数组，
当前无真实按月历史统计表，故不伪造历史；待后续接入学习记录后再改为聚合。
学生 learnCourseCount 等字段亦为历史快照，不在此 Dashboard 中改写。
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_category import CourseCategory
from app.models.student import Student
from app.models.teacher import Teacher


def build_dashboard(db: Session) -> dict:
    course_total = int(db.scalar(select(func.count(Course.id))) or 0)
    teacher_total = int(db.scalar(select(func.count(Teacher.id))) or 0)
    student_total = int(db.scalar(select(func.count(Student.id))) or 0)
    learn_total = int(db.scalar(select(func.coalesce(func.sum(Course.learn_count), 0))) or 0)

    avg_raw = db.scalar(select(func.avg(Course.completion_rate)))
    completion_rate = round(float(avg_raw)) if avg_raw is not None else 0

    category_rows = db.execute(
        select(CourseCategory.name, func.count(Course.id))
        .join(Course, Course.category_id == CourseCategory.id)
        .group_by(CourseCategory.id, CourseCategory.name)
        .order_by(CourseCategory.name.asc())
    ).all()
    # 与旧口径一致：只返回「至少有一门课」的分类
    category_pie = [{"name": name, "value": int(cnt)} for name, cnt in category_rows]

    hot_rows = db.scalars(
        select(Course).order_by(Course.learn_count.desc(), Course.id.asc()).limit(5)
    ).all()
    hot_courses = [{"name": c.name, "value": int(c.learn_count)} for c in hot_rows]

    months = [f"{i}月" for i in range(1, 13)]
    course_trend_values = [8, 12, 18, 25, 32, 40, 52, 66, 78, 90, 108, course_total + 120]
    # 无真实按月学生增长数据：保留原硬编码趋势，勿用 student_total 伪造历史
    student_trend_values = [120, 160, 210, 280, 350, 420, 510, 600, 720, 830, 950, 1100]

    return {
        "cards": {
            "courseTotal": course_total,
            "teacherTotal": teacher_total,
            "studentTotal": student_total,
            "learnTotal": learn_total,
        },
        "courseTrend": {"months": months, "values": course_trend_values},
        "studentTrend": {"months": months, "values": student_trend_values},
        "categoryPie": category_pie,
        "hotCourses": hot_courses,
        "completionRate": completion_rate,
    }
