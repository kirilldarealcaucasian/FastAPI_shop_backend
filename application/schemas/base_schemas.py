from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Id(BaseModel):
    id: int


class Config(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BookBaseS(Config):
    name: str = Field(min_length=2)
    summary: str | None
    price_per_unit: Decimal = Field(ge=1.0)
    number_in_stock: int = Field(ge=0)


class OrderBaseS(Config):
    user_id: int


class UserBaseS(Config):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: EmailStr


class ImageBaseS(Config):
    pass
