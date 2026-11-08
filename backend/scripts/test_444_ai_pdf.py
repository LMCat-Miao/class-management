"""
4.4.4 任务 B：AI PDF 解析大小限制与内容校验。

用法（在 backend 目录）：

    python scripts\\test_444_ai_pdf.py
"""

from __future__ import annotations

import io
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        raise SystemExit(1)


VALID_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def main() -> int:
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.main import app

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]

    admin = client.post("/login", json={"username": "admin", "password": "123456"}).json()
    check("admin login", admin.get("code") == 0)
    h = {"Authorization": f"Bearer {admin['data']['accessToken']}"}

    def parse(filename: str, content: bytes, course_name: str = ""):
        data = {"courseName": course_name} if course_name else None
        return client.post(
            "/ai/parse-pdf",
            headers=h,
            files={"file": (filename, io.BytesIO(content), "application/pdf")},
            data=data or {},
        )

    r = parse(f"ok_{suffix}.pdf", VALID_PDF, course_name="测试课程")
    body = r.json()
    check("valid pdf parse", body.get("code") == 0, str(body))
    check("fields summary", "summary" in (body.get("data") or {}))
    check("fields chapters", isinstance((body.get("data") or {}).get("chapters"), list))
    check("topic in summary", "测试课程" in (body["data"]["summary"] or ""))

    r = parse(f"fake_{suffix}.pdf", b"this is txt not pdf")
    check("txt as pdf rejected", r.json().get("code") == 400, str(r.json()))

    r = parse(f"broken_{suffix}.pdf", b"%PDF-1.4\nno eof here")
    check("broken pdf rejected", r.json().get("code") == 400, str(r.json()))

    r = parse(f"empty_{suffix}.pdf", b"")
    # 空文件：multipart 可能仍带空 body
    check("empty pdf rejected", r.json().get("code") == 400, str(r.json()))

    r = parse(f"tiny_{suffix}.pdf", b"%PDF")
    check("tiny pdf rejected", r.json().get("code") == 400)

    r = parse("notes.txt", VALID_PDF)
    check("non-pdf ext rejected", r.json().get("code") == 400)

    with patch.object(settings, "ai_pdf_max_bytes", 32):
        r = parse(f"big_{suffix}.pdf", VALID_PDF + b"x" * 100)
        check("oversize rejected", r.json().get("code") == 400, str(r.json()))

    # 回归：合法解析字段形状
    r = parse(f"again_{suffix}.pdf", VALID_PDF)
    d = r.json()["data"]
    check(
        "shape ok",
        all(k in d for k in ("fileName", "summary", "knowledgePoints", "chapters", "focus", "difficulties")),
    )

    print("[444-ai-pdf] all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
