from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Query, Response


MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_NUMBER = 1_000


@dataclass(frozen=True)
class Pagination:
    page: int = 1
    per_page: int = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


def pagination_params(
    page: Annotated[int, Query(ge=1, le=MAX_PAGE_NUMBER)] = 1,
    per_page: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(page=page, per_page=per_page)


def add_pagination_headers(response: Response, *, pagination: Pagination, total: int) -> None:
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(pagination.page)
    response.headers["X-Per-Page"] = str(pagination.per_page)
