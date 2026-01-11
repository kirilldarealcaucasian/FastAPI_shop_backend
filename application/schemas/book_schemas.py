from decimal import Decimal

from pydantic import BaseModel, Field

from application.schemas.base_schemas import BookBaseS


class BookIdS(BaseModel):
    id: int


class ReturnBookS(BookIdS, BookBaseS):
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


class CreateBookS(BookBaseS):
    isbn: str = Field(min_length=1)
    rating: float | None = Field(default=0, ge=0)
    discount: int | None = Field(default=0, ge=0)


class UpdateBookS(BookBaseS):
    isbn: str = Field(min_length=1)
    rating: float | None = Field(ge=0)
    discount: Decimal = Field(ge=0)


class UpdatePartiallyBookS(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    isbn: str | None = None
    description: str | None = None
    price_per_unit: float | None = Field(default=None, ge=0)
    number_in_stock: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0)
    discount: int | None = Field(default=None, ge=0)


class BookSummaryS(BaseModel):
    name: str
    count_ordered: int
    total_price: float
