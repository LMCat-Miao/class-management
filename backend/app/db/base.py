"""
ORM 基类（Declarative Base）。

说明：
- ORM（Object-Relational Mapping）把「Python 类」映射成「数据库表」。
- 所有业务表的 Model 都应继承同一个 Base，这样 Alembic 才能从
  Base.metadata 收集到全部表结构并生成迁移。
- 项目中只定义这一份 Base，避免多处 Base 导致元数据分裂。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """全部 ORM 模型的公共基类。"""

    pass
