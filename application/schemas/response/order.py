from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from pydantic import BaseModel, EmailStr, Field

from .book import BookSummaryResponse


class OrderIdResponse(BaseModel):
    id: int


class OrderSummaryResponse(BaseModel):
    username: str
    email: str
    books: list[BookSummaryResponse]


@dataclass(frozen=True)
class AssocBookResponse:
    book_id: int
    book_title: str
    authors: list[str]
    categories: list[str]
    rating: float
    discount: Decimal
    count_ordered: int
    price_per_unit: Decimal


class GetOrderResponse(BaseModel):
    order_id: int
    books: Sequence[AssocBookResponse]


class GetShortOrderResponse(BaseModel):
    owner_name: str = Field(min_length=2)
    owner_email: EmailStr
    order_id: int
    order_status: str
    total_sum: float | None = None
    order_date: datetime | None = None


class GetOrderIdResponse(GetOrderResponse):
    order_id: int
