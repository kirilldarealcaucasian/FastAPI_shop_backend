from decimal import Decimal

from pydantic import BaseModel

from ..base_schemas import BookBaseS


class CreateBookResponse(BaseModel):
    id: int
    name: str
    summary: str | None
    price_per_unit: Decimal
    number_in_stock: int
    isbn: str
    rating: float | None
    discount: Decimal


class BookIdResponse(BaseModel):
    id: int


class GetBookResponse(BookIdResponse, BookBaseS):
    isbn: str
    name: str
    categories: list[str]
    authors: list[str]
    year_of_publication: int
    language: str
    country: str
    publisher: str
    rating: float | None
    image: str
    discount: Decimal


class BookSummaryResponse(BaseModel):
    name: str
    count_ordered: int
    total_price: float


class UpdateBookResponse(BaseModel):
    isbn: str
    summary: str | None
    rating: float
    discount: Decimal
    name: str
    price_per_unit: Decimal
    number_in_stock: int
