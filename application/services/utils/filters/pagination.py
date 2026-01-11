from pydantic import BaseModel, Field


class Pagination(BaseModel):
    limit: int = Field(default=10, ge=1)
    page: int = Field(default=0, ge=0)
