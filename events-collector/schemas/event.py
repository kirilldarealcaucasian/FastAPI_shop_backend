from pydantic import BaseModel, Field


class BookEventRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_id: int | None = None
    book_id: int = Field(ge=1)
    event: str = Field(min_length=1, max_length=64)
    ts: int = Field(ge=0)
    weight: float = Field(default=1.0, gt=0)
