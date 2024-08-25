from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ShoppingSessionS(BaseModel):
    id: UUID | None = None
    user_id: int | None = None
    total: float | None = None
    expiration_time: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None