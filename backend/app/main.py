from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routers import ai, auth, course, dashboard, resource, student, teacher

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
    detail = exc.detail
    message = detail if isinstance(detail, str) else "请求失败"
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "data": None, "message": message},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "data": None,
            "message": "参数校验失败",
            "errors": exc.errors(),
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
app.include_router(resource.router)
app.include_router(ai.router)
