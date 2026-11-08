"""create students, enrollments, resources

Revision ID: 20260323_0001
Revises: 20260322_0001
Create Date: 2026-03-23

第二版迁移：学生、选课、资源元数据表。
仅 DDL，不插入演示业务数据。
执行：python -m alembic upgrade head
回滚：python -m alembic downgrade -1（仅删除本迁移三张表）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "20260323_0001"
down_revision: Union[str, None] = "20260322_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- students ----------
    op.create_table(
        "students",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("student_no", sa.String(length=64), nullable=False, comment="学号，对应 API studentNo"),
        sa.Column("name", sa.String(length=64), nullable=False, comment="姓名"),
        sa.Column("avatar", sa.String(length=512), server_default="", nullable=False, comment="头像 URL"),
        sa.Column("class_name", sa.String(length=64), server_default="", nullable=False, comment="班级"),
        sa.Column("phone", sa.String(length=32), server_default="", nullable=False, comment="手机号"),
        sa.Column(
            "learn_course_count",
            mysql.INTEGER(unsigned=True),
            server_default="0",
            nullable=False,
            comment="历史学习课程数快照",
        ),
        sa.Column(
            "finish_course_count",
            mysql.INTEGER(unsigned=True),
            server_default="0",
            nullable=False,
            comment="历史完成课程数快照",
        ),
        sa.Column(
            "progress",
            sa.SmallInteger(),
            server_default="0",
            nullable=False,
            comment="学习进度 0-100",
        ),
        sa.Column(
            "avg_completion",
            sa.SmallInteger(),
            server_default="0",
            nullable=False,
            comment="平均完成率 0-100",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            server_default="1",
            nullable=False,
            comment="1=正常 0=停用",
        ),
        sa.Column("registered_at", sa.Date(), nullable=False, comment="注册日期"),
        sa.Column(
            "recent_courses_json",
            mysql.JSON(),
            nullable=True,
            comment="recentCourses 展示快照（课程名列表），非选课关系",
        ),
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
        sa.UniqueConstraint("student_no"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_students_student_no", "students", ["student_no"], unique=False)

    # ---------- enrollments ----------
    op.create_table(
        "enrollments",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("student_id", mysql.INTEGER(unsigned=True), nullable=False, comment="学生外键"),
        sa.Column("course_id", mysql.INTEGER(unsigned=True), nullable=False, comment="课程外键"),
        sa.Column(
            "status",
            sa.SmallInteger(),
            server_default="1",
            nullable=False,
            comment="1=在读 0=退选",
        ),
        sa.Column(
            "enrolled_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="选课时间",
        ),
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
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_enrollments_student_course"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"], unique=False)
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"], unique=False)

    # ---------- resources ----------
    op.create_table(
        "resources",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("course_id", mysql.INTEGER(unsigned=True), nullable=False, comment="所属课程"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="原始文件名"),
        sa.Column("type", sa.String(length=32), server_default="其他", nullable=False, comment="资源类型"),
        sa.Column(
            "size",
            mysql.BIGINT(unsigned=True),
            server_default="0",
            nullable=False,
            comment="文件字节数",
        ),
        sa.Column("uploader", sa.String(length=64), server_default="", nullable=False, comment="上传人展示名"),
        sa.Column("uploader_user_id", mysql.INTEGER(unsigned=True), nullable=True, comment="上传用户，可空"),
        sa.Column(
            "uploaded_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="上传时间",
        ),
        sa.Column(
            "status",
            sa.SmallInteger(),
            server_default="1",
            nullable=False,
            comment="1=正常 0=停用",
        ),
        sa.Column("file_path", sa.String(length=512), nullable=True, comment="相对上传根目录的路径，可空"),
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploader_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("ix_resources_course_id", "resources", ["course_id"], unique=False)
    op.create_index("ix_resources_uploader_user_id", "resources", ["uploader_user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("resources")
    op.drop_table("enrollments")
    op.drop_table("students")
