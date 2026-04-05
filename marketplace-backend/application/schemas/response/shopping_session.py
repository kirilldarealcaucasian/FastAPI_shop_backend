from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class GetShoppingSessionResponse(BaseModel):
    id: UUID
    user_id: int | None
    total: Decimal
    expiration_time: datetime


class ShoppingSessionIdResponse(BaseModel):
    session_id: UUID
