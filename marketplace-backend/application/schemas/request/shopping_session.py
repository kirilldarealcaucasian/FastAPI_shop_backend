from datetime import datetime

from pydantic import BaseModel, Field


class CreateShoppingSessionRequest(BaseModel):
    user_id: int | None
    total: float


class UpdatePartiallyShoppingSessionRequest(BaseModel):
    total: float = Field(ge=0)
    expiration_time: datetime | None
