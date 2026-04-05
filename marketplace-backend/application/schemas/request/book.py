from decimal import Decimal

from pydantic import BaseModel, Field

from ..base_schemas import BookBaseS


class CreateBookRequest(BookBaseS):
    isbn: str = Field(min_length=1)
    rating: float | None = Field(default=0, ge=0)
    discount: int | None = Field(default=0, ge=0)


class UpdateBookRequest(BookBaseS):
    isbn: str = Field(min_length=1)
    rating: float | None = Field(ge=0)
    discount: Decimal = Field(ge=0)


class UpdatePartiallyBookRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    isbn: str | None = None
    description: str | None = None
    price_per_unit: float | None = Field(default=None, ge=0)
    number_in_stock: int | None = Field(default=None, ge=0)
    rating: float | None = Field(default=None, ge=0)
    discount: int | None = Field(default=None, ge=0)
