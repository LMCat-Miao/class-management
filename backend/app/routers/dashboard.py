from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ok
from app.db.database import get_db
from app.deps import get_current_user
from app.services.dashboard_query import build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dashboard：课程/教师/学生总量等为 MySQL 聚合；趋势数组仍为演示硬编码。"""
    _ = user
    return ok(build_dashboard(db))
