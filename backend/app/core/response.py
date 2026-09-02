from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "data": data, "message": message}


def fail(message: str = "请求失败", code: int = 1, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "data": None, "message": message},
    )
