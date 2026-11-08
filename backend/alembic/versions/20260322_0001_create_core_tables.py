"""create core tables: users, teachers, course_categories, courses

Revision ID: 20260322_0001
Revises:
Create Date: 2026-03-22

第一版迁移：创建第一期四张核心表及约束。
执行：python -m alembic upgrade head
回滚：python -m alembic downgrade -1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "20260322_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("username", sa.String(length=64), nullable=False, comment="登录用户名，唯一"),
        sa.Column("nickname", sa.String(length=64), nullable=False, comment="昵称"),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="bcrypt 密码哈希，禁止返回给前端",
        ),
        sa.Column("role", sa.String(length=32), nullable=False, comment="单角色：admin 或 teacher"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    # ---------- teachers ----------
    op.create_table(
        "teachers",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键；API 中的 teacherId 使用本字段，不是 users.id"),
        sa.Column("user_id", mysql.INTEGER(unsigned=True), nullable=True, comment="关联登录用户，可空且唯一"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="教师姓名"),
        sa.Column("avatar", sa.String(length=512), server_default="", nullable=False, comment="头像 URL"),
        sa.Column("phone", sa.String(length=32), server_default="", nullable=False, comment="手机号"),
        sa.Column("email", sa.String(length=128), server_default="", nullable=False, comment="邮箱"),
        sa.Column("title", sa.String(length=64), server_default="讲师", nullable=False, comment="职称"),
        sa.Column("status", sa.SmallInteger(), server_default="1", nullable=False, comment="1=启用，0=停用"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # ---------- course_categories ----------
    op.create_table(
        "course_categories",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=32), nullable=False, comment="分类中文名，API 仍返回该字符串"),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False, comment="排序，数值越小越靠前"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # ---------- courses ----------
    op.create_table(
        "courses",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("name", sa.String(length=128), nullable=False, comment="课程名称"),
        sa.Column("cover", sa.String(length=512), server_default="", nullable=False, comment="封面 URL"),
        sa.Column("category_id", mysql.INTEGER(unsigned=True), nullable=False, comment="分类外键"),
        sa.Column("teacher_id", mysql.INTEGER(unsigned=True), nullable=False, comment="授课教师外键"),
        sa.Column("difficulty", sa.String(length=16), server_default="初级", nullable=False, comment="难度：初级/中级/高级"),
        sa.Column("duration", mysql.INTEGER(unsigned=True), server_default="0", nullable=False, comment="时长（小时）"),
        sa.Column(
            "student_count",
            mysql.INTEGER(unsigned=True),
            server_default="0",
            nullable=False,
            comment="学生数量（展示字段）",
        ),
        sa.Column(
            "learn_count",
            mysql.INTEGER(unsigned=True),
            server_default="0",
            nullable=False,
            comment="学习人数（展示/排行字段）",
        ),
        sa.Column(
            "completion_rate",
            sa.SmallInteger(),
            server_default="0",
            nullable=False,
            comment="完成率 0～100 的整数",
        ),
        sa.Column("status", sa.SmallInteger(), server_default="1", nullable=False, comment="1=上架，0=下架"),
        # MySQL 8.x: TEXT/JSON cannot use a column DEFAULT; app-layer defaults only.
        sa.Column("intro", sa.Text(), nullable=False, comment="课程简介"),
        sa.Column(
            "chapters_json",
            mysql.JSON(),
            nullable=False,
            comment="章节数组，如 [{id, title}, ...]；API 对外叫 chapters",
        ),
        sa.Column("created_at", sa.Date(), nullable=False, comment="创建日期；API 返回 YYYY-MM-DD 字符串 createdAt"),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新时间",
        ),
        sa.CheckConstraint(
            "completion_rate >= 0 AND completion_rate <= 100",
            name="ck_courses_completion_rate",
        ),
        sa.ForeignKeyConstraint(["category_id"], ["course_categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_courses_category_id", "courses", ["category_id"], unique=False)
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_courses_teacher_id", table_name="courses")
    op.drop_index("ix_courses_category_id", table_name="courses")
    op.drop_table("courses")
    op.drop_table("course_categories")
    op.drop_table("teachers")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
