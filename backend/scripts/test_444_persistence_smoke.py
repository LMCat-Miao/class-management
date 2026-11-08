"""
4.4.4 持久化冒烟：选课 + 资源上传后重新建立会话仍可读取/下载。

用法（在 backend 目录）：

    python scripts\\test_444_persistence_smoke.py
"""

from __future__ import annotations

import io
import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


VALID_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\npersist\n"


def main() -> int:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from app.db.database import SessionLocal
    from app.main import app
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.resource import Resource
    from app.models.student import Student
    from app.services.resource_write import safe_relative_path

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    marker = f"__T444P_{suffix}__"
    student_ids: list[int] = []
    enrollment_ids: list[int] = []
    resource_ids: list[int] = []
    rel_path: str | None = None

    def cleanup() -> None:
        db = SessionLocal()
        try:
            for rid in resource_ids:
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
            for eid in enrollment_ids:
                row = db.get(Enrollment, eid)
                if row:
                    db.delete(row)
            db.commit()
            for sid in student_ids:
                row = db.get(Student, sid)
                if row:
                    db.delete(row)
            db.commit()
            print("[cleanup] done")
        except Exception as exc:
            db.rollback()
            print(f"[cleanup][WARN] {exc}")
        finally:
            db.close()

    try:
        admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
        check("login", admin.get("code") == 0)
        h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

        db = SessionLocal()
        try:
            course = db.scalar(select(Course).limit(1))
            check("course", course is not None)
            cid = course.id
        finally:
            db.close()

        st = client.post(
            "/student",
            headers=h,
            json={"name": marker, "studentNo": f"P444{suffix}", "className": "P"},
        ).json()
        check("student", st.get("code") == 0)
        sid = st["data"]["id"]
        student_ids.append(sid)

        enr = client.post(
            "/enrollment",
            headers=h,
            json={"studentId": sid, "courseId": cid},
        ).json()
        check("enroll", enr.get("code") == 0)
        enrollment_ids.append(enr["data"]["id"])

        up = client.post(
            "/resource/upload",
            headers=h,
            data={"courseId": str(cid)},
            files={"file": (f"{marker}.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        ).json()
        check("upload", up.get("code") == 0, str(up))
        rid = up["data"]["id"]
        resource_ids.append(rid)

        db = SessionLocal()
        try:
            row = db.get(Resource, rid)
            rel_path = row.file_path
            check("file exists", safe_relative_path(rel_path).is_file())
        finally:
            db.close()

        # 模拟「重启」：新 TestClient / 新请求
        client2 = TestClient(app)
        admin2 = client2.post("/login", json={"username": "admin", "password": "123456"}).json()
        h2 = {"Authorization": f"Bearer {admin2['data']['accessToken']}"}

        lst = client2.get(f"/enrollment/student/{sid}", headers=h2).json()
        check("enroll persists", lst.get("code") == 0 and any(x["id"] == enrollment_ids[0] for x in lst["data"]))

        meta = client2.get("/resource/list", headers=h2, params={"name": marker, "page": 1, "pageSize": 10}).json()
        check("resource meta persists", meta.get("code") == 0 and any(x["id"] == rid for x in meta["data"]["list"]))

        dl = client2.get(f"/resource/{rid}/download", headers=h2)
        check("download persists", dl.status_code == 200 and dl.content == VALID_PDF)
        check("disk still there", rel_path is not None and safe_relative_path(rel_path).is_file())

        print("[444-persistence-smoke] all checks passed")
        return 0
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
