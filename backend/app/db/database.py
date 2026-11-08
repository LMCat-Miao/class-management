"""
数据库连接与 Session 生命周期管理。

关键概念（给前端同学学习用）：
- Engine：连接池 + 方言的入口。负责真正跟 MySQL 说话，一般全局只创建一次。
- Session：一次「工作单元」。在 Session 里查询/修改对象，最后 commit 才落库；
  出错可 rollback 撤销本单元内未提交的改动。
- 事务（Transaction）：一组要么全部成功、要么全部失败的数据库操作。
  Session.commit() 提交当前事务；Session.rollback() 回滚。
- get_db：FastAPI 依赖注入函数，用 yield 保证请求结束时一定会关闭 Session，
  避免连接泄漏。
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine：全局单例。不要在每个 Router 里反复 create_engine。
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 取连接前先探测，降低「MySQL 已断开」导致的报错
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    # echo=True 时可在控制台打印 SQL，开发排错时再打开
    echo=False,
)

# Session 工厂：每次调用 SessionLocal() 得到一个新的 Session
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    # expire_on_commit=False：commit 后仍可读取对象属性，减少多余刷新查询
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Depends 用的数据库会话依赖。

    用法示例（后续阶段接入 Router 时）：
        def list_courses(db: Session = Depends(get_db)):
            ...

    yield 之前打开 Session；请求处理结束后（含异常）进入 finally 关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_database() -> bool:
    """执行一条简单 SQL，用于连接探测脚本。成功返回 True，失败抛出异常。"""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
