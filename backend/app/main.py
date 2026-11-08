from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# 导入 settings 时会执行生产环境 SECRET_KEY 校验（见 app.core.config.validate_settings）
from app.core.config import settings
from app.routers import ai, auth, course, dashboard, enrollment, resource, student, teacher

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    """
    HTTPException → 统一 JSON。
    detail 可为 str，或 dict{"message", "error?"}（用于稳定错误标识）。
    body.code 与 HTTP status_code 对齐。
    """
    detail = exc.detail
    error: str | None = None
    if isinstance(detail, dict):
        message = str(detail.get("message") or "请求失败")
        raw_err = detail.get("error")
        error = str(raw_err) if raw_err else None
    elif isinstance(detail, str):
        message = detail
    else:
        message = "请求失败"

    content: dict = {
        "code": exc.status_code,
        "data": None,
        "message": message,
    }
    if error:
        content["error"] = error
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    # 不向客户端返回 errors 明细，避免泄露内部字段路径
    _ = exc
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "data": None,
            "message": "参数校验失败",
        },
    )


@app.get("/health")
def health():
    return {"code": 0, "data": True, "message": "ok"}


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(course.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(enrollment.router)
app.include_router(resource.router)
app.include_router(ai.router)
