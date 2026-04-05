from pydantic import BaseModel, Field

__all__ = "BookFilter" "Pagination"


class BookFilterS(BaseModel):
    order_by: str | None = None
    filterby: str | None = None
    page: int = Field(ge=0, default=0)
    limit: int = Field(ge=1, default=5)


class PaginationS(BaseModel):
    page: int = Field(ge=0, default=0)
    limit: int = Field(ge=1, default=5)
