from datetime import datetime
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateShoppingSessionS(BaseModel):
    user_id: int | None
    total: float


class ReturnShoppingSessionS(BaseModel):
    id: UUID
    user_id: int | None
    total: Decimal
    expiration_time: datetime


class UpdatePartiallyShoppingSessionS(BaseModel):
    total: float = Field(ge=0)
    expiration_time: datetime | None


class ShoppingSessionIdS(BaseModel):
    session_id: UUID
