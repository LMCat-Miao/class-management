from fastapi import APIRouter, Depends

from app.core.response import ok
from app.data.store import COURSES, STUDENTS, TEACHERS
from app.deps import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    _ = user
    months = [f"{i}月" for i in range(1, 13)]
    category_map: dict[str, int] = {}
    for course in COURSES:
        category_map[course["category"]] = category_map.get(course["category"], 0) + 1

    hot = sorted(COURSES, key=lambda c: c["learnCount"], reverse=True)[:5]
    avg_completion = (
        round(sum(c["completionRate"] for c in COURSES) / len(COURSES))
        if COURSES
        else 0
    )

    return ok(
        {
            "cards": {
                "courseTotal": len(COURSES),
                "teacherTotal": len(TEACHERS),
                "studentTotal": max(5200, len(STUDENTS)),
                "learnTotal": sum(c["learnCount"] for c in COURSES),
            },
            "courseTrend": {
                "months": months,
                "values": [8, 12, 18, 25, 32, 40, 52, 66, 78, 90, 108, len(COURSES) + 120],
            },
            "studentTrend": {
                "months": months,
                "values": [120, 160, 210, 280, 350, 420, 510, 600, 720, 830, 950, 1100],
            },
            "categoryPie": [
                {"name": name, "value": value} for name, value in category_map.items()
            ],
            "hotCourses": [{"name": c["name"], "value": c["learnCount"]} for c in hot],
            "completionRate": avg_completion,
        }
    )
