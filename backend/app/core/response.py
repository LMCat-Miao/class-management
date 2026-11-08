"""
统一 API 响应。

约定：
- 成功：HTTP 200（或业务自定），body.code = 0
- 失败：HTTP status_code 表示 HTTP 语义；body.code 与 status_code 对齐（业务错误码）
- 可选 error：稳定机器可读标识（如 ACCOUNT_DISABLED），供前端区分处理
"""

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "data": data, "message": message}


def fail(
    message: str = "请求失败",
    *,
    code: int | None = None,
    status_code: int = 400,
    error: str | None = None,
) -> JSONResponse:
    """
    业务失败响应。

    body.code 默认等于 HTTP status_code，避免与「默认 code=1」混用。
    若显式传入 code，则以传入值为准（须与语义一致，通常等于 status_code）。
    """
    body_code = status_code if code is None else code
    content: dict[str, Any] = {
        "code": body_code,
        "data": None,
        "message": message,
    }
    if error:
        content["error"] = error
    return JSONResponse(status_code=status_code, content=content)
