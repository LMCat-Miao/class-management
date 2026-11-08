"""
统一测试入口（Windows CMD 友好）。

必须在 backend 目录执行，以保证 .env 与相对路径一致：

    cd backend
    .venv\\Scripts\\activate
    python scripts\\run_tests.py --list
    python scripts\\run_tests.py
    python scripts\\run_tests.py --safe
    python scripts\\run_tests.py --category security --include-db-write
    python scripts\\run_tests.py --category database --include-db-write
    python scripts\\run_tests.py --category api --include-db-write
    python scripts\\run_tests.py --category file --include-db-write

说明：
- 默认 / --safe：仅非写库脚本（配置校验、只读连接探测）。
- 写库脚本需显式 --include-db-write；使用独立测试数据并 cleanup，仍勿对生产库执行。
- 不包含 seed_data / alembic / migrate_*。
- 拉起临时 uvicorn 的重启脚本需额外 --include-restart。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BACKEND_ROOT / "scripts"

# 保证可 import app.*（与各 test_*.py 一致）
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class TestCase:
    script: str
    categories: tuple[str, ...]
    db_write: bool = False
    needs_restart: bool = False
    note: str = ""


CATALOG: list[TestCase] = [
    TestCase(
        "test_config_security.py",
        ("security", "safe"),
        db_write=False,
        note="APP_ENV/SECRET_KEY；不访问 MySQL",
    ),
    TestCase(
        "test_db_connection.py",
        ("database", "safe"),
        db_write=False,
        note="只读探测 MySQL 连接与库名",
    ),
    TestCase(
        "test_auth_mysql.py",
        ("security", "api"),
        db_write=True,
        note="登录 JWT / userInfo",
    ),
    TestCase(
        "test_auth_account_status.py",
        ("security", "api"),
        db_write=True,
        note="教师停用 ACCOUNT_DISABLED",
    ),
    TestCase(
        "test_course_list_acl.py",
        ("security", "api"),
        db_write=True,
        note="课程列表 ACL",
    ),
    TestCase(
        "test_course_detail_acl.py",
        ("security", "api"),
        db_write=True,
        note="课程详情 ACL",
    ),
    TestCase(
        "test_student_acl.py",
        ("security", "api", "database"),
        db_write=True,
        note="学生可见范围 ACL",
    ),
    TestCase(
        "test_resource_acl.py",
        ("security", "api", "file"),
        db_write=True,
        note="资源列表/上传/下载 ACL",
    ),
    TestCase(
        "test_444_upload_security.py",
        ("security", "file", "api"),
        db_write=True,
        note="上传内容校验/伪装/超限/清理",
    ),
    TestCase(
        "test_444_ai_pdf.py",
        ("security", "api"),
        db_write=False,
        note="AI PDF 校验（登录读库，不写业务表）",
    ),
    TestCase(
        "test_course_read_mysql.py",
        ("database", "api"),
        db_write=True,
        note="课程只读查询冒烟（可能依赖库内数据）",
    ),
    TestCase(
        "test_course_create_mysql.py",
        ("database", "api"),
        db_write=True,
        note="课程创建",
    ),
    TestCase(
        "test_course_update_mysql.py",
        ("database", "api"),
        db_write=True,
        note="课程更新",
    ),
    TestCase(
        "test_course_status_mysql.py",
        ("database", "api"),
        db_write=True,
        note="课程上下架",
    ),
    TestCase(
        "test_course_delete_mysql.py",
        ("database", "api", "file"),
        db_write=True,
        note="课程删除与资源清理",
    ),
    TestCase(
        "test_course_create_status_validation.py",
        ("api", "database"),
        db_write=True,
        note="创建 status 校验",
    ),
    TestCase(
        "test_course_update_status_validation.py",
        ("api", "database"),
        db_write=True,
        note="更新 status 校验",
    ),
    TestCase(
        "test_teacher_mysql.py",
        ("database", "api"),
        db_write=True,
        note="教师 CRUD",
    ),
    TestCase(
        "test_dashboard_mysql.py",
        ("database", "api"),
        db_write=False,
        note="Dashboard COUNT（只读聚合）",
    ),
    TestCase(
        "test_443_paging_api.py",
        ("database", "api", "file"),
        db_write=True,
        note="SQL 分页 / enrollment JOIN / 错误码",
    ),
    TestCase(
        "test_444_enrollment_api.py",
        ("database", "api"),
        db_write=True,
        note="选课创建/退选/恢复与权限",
    ),
    TestCase(
        "test_433_persistence.py",
        ("database", "api", "file"),
        db_write=True,
        note="学生/选课/资源持久化",
    ),
    TestCase(
        "test_444_persistence_smoke.py",
        ("database", "api", "file"),
        db_write=True,
        note="选课+资源下载持久化冒烟",
    ),
    TestCase(
        "test_upload_failure.py",
        ("file", "security", "api"),
        db_write=True,
        note="上传事务失败清理",
    ),
    TestCase(
        "test_433_restart_persistence.py",
        ("database", "file"),
        db_write=True,
        needs_restart=True,
        note="临时拉起 uvicorn 验证重启后文件仍在",
    ),
]


def _python_exe() -> str:
    return sys.executable


def _matches_category(case: TestCase, category: str | None, safe_mode: bool) -> bool:
    if safe_mode or category == "safe":
        return "safe" in case.categories
    if category is None:
        return True
    return category in case.categories


def _skip_reason(
    case: TestCase, *, include_db_write: bool, include_restart: bool, safe_mode: bool
) -> str | None:
    if safe_mode:
        return None
    if case.needs_restart and not include_restart:
        return "需要 --include-restart"
    if case.db_write and not include_db_write:
        return "需要 --include-db-write"
    return None


def _print_list() -> None:
    print(f"BACKEND_ROOT = {BACKEND_ROOT}")
    print(f"{'SCRIPT':<42} {'WRITE':<6} {'CATS':<28} NOTE")
    print("-" * 110)
    for case in CATALOG:
        cats = ",".join(case.categories)
        flag = "Y" if case.db_write else "N"
        extra = " [restart]" if case.needs_restart else ""
        print(f"{case.script:<42} {flag:<6} {cats:<28} {case.note}{extra}")
    print()
    print("前端检查（不在本入口内）：仓库根目录 npm run typecheck / npm run build")
    print("禁止混入：seed_data.py / alembic / migrate_*")


def _run_one(case: TestCase) -> int:
    script_path = SCRIPTS_DIR / case.script
    if not script_path.is_file():
        print(f"MISS  {case.script}  (file not found)")
        return 1
    print(f"\n======== RUN {case.script} ========")
    proc = subprocess.run(
        [_python_exe(), str(script_path)],
        cwd=str(BACKEND_ROOT),
    )
    return int(proc.returncode)


def _assert_db_target() -> int:
    """写库或需连库时确认目标为 class_management@3306。"""
    try:
        from app.core.config import settings

        print(f"db      = {settings.db_host}:{settings.db_port}/{settings.db_name}")
        if settings.db_name != "class_management" or int(settings.db_port) != 3306:
            print(
                "[ABORT] 仅允许测试库 class_management @ 3306；"
                f"当前 {settings.db_name} @ {settings.db_port}"
            )
            return 2
        if settings.db_host not in ("127.0.0.1", "localhost"):
            print(f"[ABORT] 仅允许本机 MySQL，当前 host={settings.db_host}")
            return 2
    except Exception as exc:
        print(f"[ABORT] 无法加载 settings: {exc}")
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backend smoke test runner（不含 Seed / Alembic / migrate）"
    )
    parser.add_argument("--list", action="store_true", help="列出测试，不执行")
    parser.add_argument(
        "--safe",
        action="store_true",
        help="仅非写库脚本（与无参数默认行为相同）",
    )
    parser.add_argument(
        "--category",
        choices=("security", "database", "api", "file", "safe"),
        help="按类别执行",
    )
    parser.add_argument(
        "--include-db-write",
        action="store_true",
        help="显式允许写库测试",
    )
    parser.add_argument(
        "--include-restart",
        action="store_true",
        help="允许临时 uvicorn 重启持久化测试",
    )
    args = parser.parse_args(argv)

    if args.list:
        _print_list()
        return 0

    safe_mode = args.safe or args.category is None or args.category == "safe"
    if args.category and args.category != "safe":
        safe_mode = False

    selected: list[tuple[TestCase, str | None]] = []
    for case in CATALOG:
        if not _matches_category(case, args.category, safe_mode):
            continue
        skip = _skip_reason(
            case,
            include_db_write=args.include_db_write,
            include_restart=args.include_restart,
            safe_mode=safe_mode,
        )
        selected.append((case, skip))

    if not selected:
        print("没有匹配的测试用例。使用 --list 查看。")
        return 1

    print(f"cwd     = {BACKEND_ROOT}")
    print(f"python  = {_python_exe()}")
    print(f"mode    = {'safe' if safe_mode else f'category={args.category}'}")

    needs_db = any(
        skip is None and (case.db_write or case.script != "test_config_security.py")
        for case, skip in selected
    )
    if needs_db:
        code = _assert_db_target()
        if code:
            return code

    passed = failed = skipped = 0
    for case, skip in selected:
        if skip:
            print(f"SKIP  {case.script}  ({skip})")
            skipped += 1
            continue
        code = _run_one(case)
        if code == 0:
            print(f"PASS  {case.script}")
            passed += 1
        else:
            print(f"FAIL  {case.script}  exit={code}")
            failed += 1

    print("\n======== SUMMARY ========")
    print(
        f"PASS={passed}  FAIL={failed}  SKIP={skipped}  "
        f"TOTAL={passed + failed + skipped}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
