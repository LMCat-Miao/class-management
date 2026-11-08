"""ORM 模型导出。导入本包即可将全部表注册到 Base.metadata。"""

from app.models.course import Course
from app.models.course_category import CourseCategory
from app.models.enrollment import Enrollment
from app.models.resource import Resource
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User

__all__ = [
    "User",
    "Teacher",
    "CourseCategory",
    "Course",
    "Student",
    "Enrollment",
    "Resource",
]
