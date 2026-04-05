from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)

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
    model_config = ConfigDict(from_attributes=True)

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

    @field_validator("categories", mode="before")
    @classmethod
    def extract_category_names(cls, v: list) -> list[str]:
        return [c.name for c in v] if v else []

    @field_validator("authors", mode="before")
    @classmethod
    def extract_author_names(cls, v: list):
        return [a.name for a in v] if v else []


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
