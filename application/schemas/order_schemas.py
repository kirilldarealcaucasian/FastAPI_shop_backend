from datetime import datetime
from decimal import Decimal
from typing import TypeAlias
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from application.schemas.base_schemas import OrderBaseS
from application.schemas.book_schemas import BookSummaryS

Category: TypeAlias = str


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


class AssocBookS(BaseModel):
    book_id: int
    book_title: str = Field(min_length=2)
    authors: list[str]
    categories: list[Category]
    rating: float = Field(ge=0, default=0)
    discount: Decimal = Field(ge=0)
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
    price: float = Field(ge=0.0)
