from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OrderS(BaseModel):
    user_id: int | None = None
    order_status: str | None = None
    order_date: datetime | None = None
    total_sum: float | None = None
    payment_id: UUID | None = None