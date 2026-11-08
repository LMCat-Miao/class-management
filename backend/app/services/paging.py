"""SQL 分页结果封装（与原 store.paginate 响应形状一致）。"""

from __future__ import annotations

from typing import Any


def normalize_page(page: int = 1, page_size: int = 10) -> tuple[int, int]:
    page = max(int(page or 1), 1)
    page_size = max(int(page_size or 10), 1)
    return page, page_size


def page_payload(items: list[Any], total: int, page: int, page_size: int) -> dict:
    page, page_size = normalize_page(page, page_size)
    return {
        "list": items,
        "total": int(total),
        "page": page,
        "pageSize": page_size,
    }
