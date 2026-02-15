from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from ..schemas.base_schemas import OrderBaseS
from ..schemas.book_schemas import BookSummaryS
from dataclasses import dataclass


class CreateOrderS(OrderBaseS):
    order_status: str | None = None


class OrderIdS(BaseModel):
    id: int


class UpdateOrderS(OrderBaseS):
    pass


class UpdatePartiallyOrderS(BaseModel):
    order_status: str | None
    order_date: datetime | None = None
    total_sum: float | None = Field(default=0, ge=0)


class OrderSummaryS(BaseModel):
    username: str
    email: str
    books: list[BookSummaryS]


@dataclass(frozen=True)
class AssocBookS:
    book_id: int
    book_title: str
    authors: list[str]
    categories: list[str]
    rating: float
    discount: Decimal
    count_ordered: int
    price_per_unit: Decimal


class ReturnOrderS(BaseModel):
    order_id: int
    books: list[AssocBookS]


class ShortenedReturnOrderS(BaseModel):
    owner_name: str = Field(min_length=2)
    owner_email: EmailStr
    order_id: int
    order_status: str
    total_sum: float | None = None
    order_date: datetime | None = None


class ReturnOrderIdS(ReturnOrderS):
    order_id: int


class AddBookToOrderS(BaseModel):
    book_id: UUID
    count_ordered: int = Field(ge=1)


class OrderItemS(BaseModel):
    book_name: str = Field(min_length=2)
    quantity: int = Field(ge=1)
    price: Decimal = Field(ge=0.0)
