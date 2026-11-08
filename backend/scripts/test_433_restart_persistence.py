"""
4.3.3.6 服务重启持久化验证。

1) 创建测试学生 / 选课 / 上传文件
2) 关闭 uvicorn 子进程并重新启动
3) 再次查询并下载
4) 清理测试数据与文件

用法：

    python scripts\\test_433_restart_persistence.py
"""

from __future__ import annotations

import io
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "127.0.0.1"
PORT = 8765
BASE = f"http://{HOST}:{PORT}"


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise AssertionError(name)


def wait_ready(client: httpx.Client, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = client.get(f"{BASE}/health")
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.4)
    raise RuntimeError("server not ready")


def start_server() -> subprocess.Popen:
    py = BACKEND_ROOT / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)
    proc = subprocess.Popen(
        [
            str(py),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=str(BACKEND_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main() -> int:
    from sqlalchemy import select

    from app.db.database import SessionLocal
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.resource import Resource
    from app.models.student import Student
    from app.services.resource_write import safe_relative_path

    suffix = uuid.uuid4().hex[:8]
    marker = f"__T433R_{suffix}__"
    sid = eid = rid = None
    course_id = None
    file_rel = None
    proc: subprocess.Popen | None = None

    def cleanup_db() -> None:
        db = SessionLocal()
        try:
            if rid is not None:
                row = db.get(Resource, rid)
                if row:
                    rel = row.file_path
                    db.delete(row)
                    db.commit()
                    if rel:
                        try:
                            p = safe_relative_path(rel)
                            if p.is_file():
                                p.unlink()
                        except Exception:
                            pass
            if eid is not None:
                row = db.get(Enrollment, eid)
                if row:
                    db.delete(row)
                    db.commit()
            if sid is not None:
                row = db.get(Student, sid)
                if row:
                    db.delete(row)
                    db.commit()
        finally:
            db.close()
        print("[cleanup] test rows/files removed")

    try:
        db = SessionLocal()
        try:
            course = db.scalar(select(Course).limit(1))
            check("course exists", course is not None)
            course_id = course.id
        finally:
            db.close()

        proc = start_server()
        with httpx.Client(timeout=30.0) as client:
            wait_ready(client)
            login = client.post(f"{BASE}/login", json={"username": "admin", "password": "123456"}).json()
            check("login", login.get("code") == 0)
            h = {"Authorization": f"Bearer {login['data']['accessToken']}"}

            create = client.post(
                f"{BASE}/student",
                headers=h,
                json={"name": marker, "studentNo": f"R433{suffix}", "className": "重启班"},
            ).json()
            check("create student", create.get("code") == 0)
            sid = create["data"]["id"]

            enr = client.post(
                f"{BASE}/enrollment",
                headers=h,
                json={"studentId": sid, "courseId": course_id},
            ).json()
            check("create enrollment", enr.get("code") == 0)
            eid = enr["data"]["id"]

            up = client.post(
                f"{BASE}/resource/upload",
                headers=h,
                data={"courseId": str(course_id)},
                files={
                    "file": (
                        "restart.pdf",
                        io.BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + b"restart " * 20),
                        "application/pdf",
                    )
                },
            ).json()
            check("upload resource", up.get("code") == 0, str(up.get("message")))
            rid = up["data"]["id"]

            db = SessionLocal()
            try:
                row = db.get(Resource, rid)
                file_rel = row.file_path
                check("file_path set", bool(file_rel))
            finally:
                db.close()

            print(f"[info] sid={sid} eid={eid} rid={rid} file={file_rel}")

        # restart
        stop_server(proc)
        proc = None
        time.sleep(1)
        proc = start_server()

        with httpx.Client(timeout=30.0) as client:
            wait_ready(client)
            login = client.post(f"{BASE}/login", json={"username": "admin", "password": "123456"}).json()
            h = {"Authorization": f"Bearer {login['data']['accessToken']}"}

            st = client.get(f"{BASE}/student/{sid}", headers=h).json()
            check("student persists", st.get("code") == 0 and st["data"]["name"] == marker)

            el = client.get(f"{BASE}/enrollment/student/{sid}", headers=h).json()
            check(
                "enrollment persists",
                el.get("code") == 0 and any(x["id"] == eid for x in el["data"]),
            )

            rl = client.get(f"{BASE}/resource/list", headers=h, params={"courseId": course_id}).json()
            check(
                "resource persists",
                rl.get("code") == 0 and any(x["id"] == rid for x in rl["data"]["list"]),
            )

            dl = client.get(f"{BASE}/resource/{rid}/download", headers=h)
            check("download after restart", dl.status_code == 200 and b"%PDF" in dl.content)

        print("=== RESTART PERSISTENCE: PASS ===")
        return 0
    except Exception as exc:
        print(f"=== RESTART PERSISTENCE: FAIL ({exc}) ===")
        return 1
    finally:
        if proc is not None:
            stop_server(proc)
        cleanup_db()


if __name__ == "__main__":
    raise SystemExit(main())
