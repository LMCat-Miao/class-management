"""
MySQL 基础演示数据 Seed（第二阶段）。

在 Windows CMD（已激活 venv，且位于 backend 目录）执行：

    python scripts\\seed_data.py

幂等规则：
- users：按 username 查找；已存在则跳过（不覆盖 password_hash）
- teachers：按 name 查找；已存在则跳过档案字段；仅补全「张老师 ↔ teacher 用户」绑定
- course_categories：按 name 查找；已存在则跳过
- courses：仅当表为空时批量插入；已有任意行则整批跳过

本脚本不会 DROP 表，也不会删除已有业务数据。
请勿在代码中硬编码数据库密码；连接信息来自 backend/.env。
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# 演示数据（与原 app/data/store.py 种子对齐；不 import store，避免加载内存全局状态）
# ---------------------------------------------------------------------------

DEMO_PASSWORD = "123456"

USERS_SEED = [
    {
        "username": "admin",
        "nickname": "系统管理员",
        "role": "admin",
    },
    {
        "username": "teacher",
        "nickname": "张老师",
        "role": "teacher",
    },
]

TEACHERS_SEED = [
    {
        "name": "张老师",
        "avatar": "",
        "phone": "13800000001",
        "email": "zhang@example.com",
        "title": "高级讲师",
        "status": 1,
    },
    {
        "name": "李老师",
        "avatar": "",
        "phone": "13800000002",
        "email": "li@example.com",
        "title": "副教授",
        "status": 1,
    },
    {
        "name": "王老师",
        "avatar": "",
        "phone": "13800000003",
        "email": "wang@example.com",
        "title": "讲师",
        "status": 1,
    },
    {
        "name": "赵老师",
        "avatar": "",
        "phone": "13800000004",
        "email": "zhao@example.com",
        "title": "助教",
        "status": 0,
    },
]

# teacher 登录账号绑定的教师姓名
TEACHER_USER_BIND_NAME = "张老师"

CATEGORIES_SEED = [
    {"name": "前端", "sort_order": 1},
    {"name": "AI", "sort_order": 2},
    {"name": "Python", "sort_order": 3},
    {"name": "算法", "sort_order": 4},
    {"name": "Java", "sort_order": 5},
]

# category / teacher 用中文名，写入前解析成外键 id
COURSES_SEED = [
    {
        "name": "Vue3企业级开发",
        "cover": "https://picsum.photos/seed/vue3/160/90",
        "category": "前端",
        "teacher": "张老师",
        "difficulty": "中级",
        "duration": 36,
        "student_count": 328,
        "learn_count": 3000,
        "completion_rate": 82,
        "status": 1,
        "intro": "系统讲解 Vue3 Composition API、Pinia、Router、Axios 企业级实践。",
        "created_at": date(2025, 1, 12),
        "chapters_json": [
            {"id": 1, "title": "第一章 Vue3基础"},
            {"id": 2, "title": "第二章 Composition API"},
            {"id": 3, "title": "第三章 Pinia"},
            {"id": 4, "title": "第四章 Router"},
            {"id": 5, "title": "第五章 Axios"},
        ],
    },
    {
        "name": "AI大模型应用开发",
        "cover": "https://picsum.photos/seed/ai/160/90",
        "category": "AI",
        "teacher": "李老师",
        "difficulty": "高级",
        "duration": 48,
        "student_count": 256,
        "learn_count": 5000,
        "completion_rate": 76,
        "status": 1,
        "intro": "覆盖 Prompt、RAG、Agent 与企业落地案例。",
        "created_at": date(2025, 2, 8),
        "chapters_json": [
            {"id": 1, "title": "第一章 大模型概览"},
            {"id": 2, "title": "第二章 Prompt Engineering"},
            {"id": 3, "title": "第三章 RAG 实战"},
        ],
    },
    {
        "name": "算法与数据结构",
        "cover": "https://picsum.photos/seed/algo/160/90",
        "category": "算法",
        "teacher": "王老师",
        "difficulty": "中级",
        "duration": 40,
        "student_count": 412,
        "learn_count": 4000,
        "completion_rate": 71,
        "status": 1,
        "intro": "常见数据结构与算法题型精讲。",
        "created_at": date(2025, 3, 1),
        "chapters_json": [
            {"id": 1, "title": "第一章 复杂度分析"},
            {"id": 2, "title": "第二章 数组与链表"},
            {"id": 3, "title": "第三章 树与图"},
        ],
    },
    {
        "name": "Python数据分析",
        "cover": "https://picsum.photos/seed/python/160/90",
        "category": "Python",
        "teacher": "李老师",
        "difficulty": "初级",
        "duration": 28,
        "student_count": 198,
        "learn_count": 2800,
        "completion_rate": 80,
        "status": 0,
        "intro": "Pandas、NumPy 与可视化入门。",
        "created_at": date(2025, 3, 20),
        "chapters_json": [
            {"id": 1, "title": "第一章 Python基础"},
            {"id": 2, "title": "第二章 Pandas"},
        ],
    },
    {
        "name": "前端工程化实践",
        "cover": "https://picsum.photos/seed/fe/160/90",
        "category": "前端",
        "teacher": "张老师",
        "difficulty": "高级",
        "duration": 32,
        "student_count": 166,
        "learn_count": 2200,
        "completion_rate": 74,
        "status": 1,
        "intro": "Vite、CI/CD、组件库与性能优化。",
        "created_at": date(2025, 4, 5),
        "chapters_json": [
            {"id": 1, "title": "第一章 工程化概览"},
            {"id": 2, "title": "第二章 构建与部署"},
        ],
    },
    {
        "name": "JavaScript进阶",
        "cover": "https://picsum.photos/seed/js/160/90",
        "category": "前端",
        "teacher": "张老师",
        "difficulty": "中级",
        "duration": 30,
        "student_count": 366,
        "learn_count": 3500,
        "completion_rate": 85,
        "status": 1,
        "intro": "闭包、原型、异步与设计模式。",
        "created_at": date(2025, 5, 10),
        "chapters_json": [
            {"id": 1, "title": "第一章 作用域与闭包"},
            {"id": 2, "title": "第二章 异步编程"},
        ],
    },
    {
        "name": "Java企业开发",
        "cover": "https://picsum.photos/seed/java/160/90",
        "category": "Java",
        "teacher": "赵老师",
        "difficulty": "中级",
        "duration": 45,
        "student_count": 180,
        "learn_count": 1900,
        "completion_rate": 68,
        "status": 1,
        "intro": "Spring Boot 与微服务入门。",
        "created_at": date(2025, 6, 1),
        "chapters_json": [
            {"id": 1, "title": "第一章 Spring Boot"},
            {"id": 2, "title": "第二章 数据访问"},
        ],
    },
    {
        "name": "机器学习基础",
        "cover": "https://picsum.photos/seed/ml/160/90",
        "category": "AI",
        "teacher": "李老师",
        "difficulty": "中级",
        "duration": 42,
        "student_count": 240,
        "learn_count": 4200,
        "completion_rate": 73,
        "status": 1,
        "intro": "监督学习、特征工程与模型评估。",
        "created_at": date(2025, 7, 15),
        "chapters_json": [
            {"id": 1, "title": "第一章 机器学习概览"},
            {"id": 2, "title": "第二章 回归与分类"},
        ],
    },
]


def _seed_categories(db: Session) -> tuple[int, int]:
    from app.models import CourseCategory

    created = skipped = 0
    for item in CATEGORIES_SEED:
        exists = db.scalar(
            select(CourseCategory).where(CourseCategory.name == item["name"])
        )
        if exists:
            skipped += 1
            continue
        db.add(
            CourseCategory(
                name=item["name"],
                sort_order=item["sort_order"],
            )
        )
        created += 1
    db.flush()
    return created, skipped


def _seed_users(db: Session) -> tuple[int, int]:
    """按 username 幂等插入；已存在绝不改 password_hash。"""
    from app.core.security import hash_password
    from app.models import User

    created = skipped = 0
    for item in USERS_SEED:
        exists = db.scalar(select(User).where(User.username == item["username"]))
        if exists:
            skipped += 1
            continue
        db.add(
            User(
                username=item["username"],
                nickname=item["nickname"],
                role=item["role"],
                # 仅新建时哈希；已存在用户不会走到这里
                password_hash=hash_password(DEMO_PASSWORD),
            )
        )
        created += 1
    db.flush()
    return created, skipped


def _seed_teachers(db: Session) -> tuple[int, int, int]:
    """
    按 name 幂等插入教师。

    返回 (created, skipped, bind_updated)：
    bind_updated 表示「张老师.user_id」被新建或修正为 teacher 用户的次数（0 或 1）。
    """
    from app.models import Teacher, User

    created = skipped = 0
    for item in TEACHERS_SEED:
        exists = db.scalar(select(Teacher).where(Teacher.name == item["name"]))
        if exists:
            skipped += 1
            continue
        db.add(
            Teacher(
                name=item["name"],
                avatar=item["avatar"],
                phone=item["phone"],
                email=item["email"],
                title=item["title"],
                status=item["status"],
                user_id=None,
            )
        )
        created += 1
    db.flush()

    # 绑定：teacher 用户 ↔ 张老师（teachers.user_id = users.id）
    bind_updated = 0
    teacher_user = db.scalar(select(User).where(User.username == "teacher"))
    zhang = db.scalar(select(Teacher).where(Teacher.name == TEACHER_USER_BIND_NAME))
    if teacher_user and zhang:
        if zhang.user_id != teacher_user.id:
            zhang.user_id = teacher_user.id
            bind_updated = 1
    db.flush()
    return created, skipped, bind_updated


def _seed_courses(db: Session) -> tuple[int, int]:
    """仅当 courses 为空时插入全部演示课。"""
    from app.models import Course, CourseCategory, Teacher

    total = db.scalar(select(func.count()).select_from(Course)) or 0
    if total > 0:
        return 0, len(COURSES_SEED)

    categories = {
        row.name: row.id
        for row in db.scalars(select(CourseCategory)).all()
    }
    teachers = {
        row.name: row.id
        for row in db.scalars(select(Teacher)).all()
    }

    created = 0
    for item in COURSES_SEED:
        category_id = categories.get(item["category"])
        teacher_id = teachers.get(item["teacher"])
        if category_id is None or teacher_id is None:
            raise RuntimeError(
                f"course '{item['name']}' missing FK: "
                f"category={item['category']!r} teacher={item['teacher']!r}"
            )
        rate = int(item["completion_rate"])
        if rate < 0 or rate > 100:
            raise RuntimeError(
                f"course '{item['name']}' invalid completion_rate={rate}"
            )
        db.add(
            Course(
                name=item["name"],
                cover=item["cover"],
                category_id=category_id,
                teacher_id=teacher_id,
                difficulty=item["difficulty"],
                duration=item["duration"],
                student_count=item["student_count"],
                learn_count=item["learn_count"],
                completion_rate=rate,
                status=item["status"],
                intro=item["intro"],
                chapters_json=list(item["chapters_json"]),
                created_at=item["created_at"],
            )
        )
        created += 1
    db.flush()
    return created, 0


def run_seed(db: Session) -> None:
    cat_c, cat_s = _seed_categories(db)
    print(f"[categories] created={cat_c} skipped={cat_s}")

    user_c, user_s = _seed_users(db)
    print(f"[users] created={user_c} skipped={user_s}")

    tea_c, tea_s, bind_u = _seed_teachers(db)
    print(
        f"[teachers] created={tea_c} skipped={tea_s} "
        f"zhang_user_bind_updated={bind_u}"
    )

    course_c, course_s = _seed_courses(db)
    if course_c == 0 and course_s > 0:
        print(
            f"[courses] created=0 skipped={course_s} "
            "(table not empty; demo courses not inserted)"
        )
    else:
        print(f"[courses] created={course_c} skipped={course_s}")


def main() -> int:
    from app.core.config import settings
    from app.db.database import SessionLocal

    print(
        f"[seed] target db={settings.db_name} "
        f"host={settings.db_host}:{settings.db_port}"
    )

    db = SessionLocal()
    try:
        run_seed(db)
        db.commit()
        print("[seed] OK committed")
        return 0
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"[seed] FAIL rolled back: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
