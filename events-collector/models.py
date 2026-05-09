from pydantic import BaseModel, Field


class BookEventRequest(BaseModel):
    book_id: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=64)
    ts: int = Field(ge=0)


__all__ = ("BookEventRequest",)
