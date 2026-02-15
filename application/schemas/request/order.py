from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ..base_schemas import OrderBaseS


class CreateOrderRequest(OrderBaseS):
    order_status: str | None = None


class UpdateOrderRequest(OrderBaseS):
    pass


class UpdatePartiallyOrderRequest(BaseModel):
    order_status: str | None
    order_date: datetime | None = None
    total_sum: Decimal | None = Field(default=Decimal(0), ge=0)


class AddBookToOrderRequest(BaseModel):
    book_id: UUID
    count_ordered: int = Field(ge=1)


class OrderItemRequest(BaseModel):
    book_name: str = Field(min_length=2)
    quantity: int = Field(ge=1)
    price: Decimal = Field(ge=0.0)
