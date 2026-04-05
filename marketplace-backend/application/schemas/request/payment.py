from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from .order import OrderItemRequest


class CreatePaymentRequest(BaseModel):
    customer_full_name: str = Field(min_length=3)
    customer_email: EmailStr
    total_amount: Decimal = Field(ge=1.0)
    currency: str = Field(default="RUB", min_length=2)
    description: str
    items: list[OrderItemRequest] | None = Field(default=None)
