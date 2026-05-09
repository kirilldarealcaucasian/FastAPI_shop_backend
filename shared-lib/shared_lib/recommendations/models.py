from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import BookEventAction


class UserSessionLinkMessage(BaseModel):
    session_id: UUID
    user_id: int
    session_expiration_time: datetime


class BookEventMessage(BaseModel):
    # if user_id is not None, meaning the event came from the logged-in user
    session_id: UUID
    session_expiration_time: datetime
    user_id: int | None = None
    book_id: int = Field(ge=1)
    event: BookEventAction
    ts: int = Field(ge=0)
    weight: float = Field(gt=0)


__all__ = (
    "BookEventMessage",
    "UserSessionLinkMessage",
)
