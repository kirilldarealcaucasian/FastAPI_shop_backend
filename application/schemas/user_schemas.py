from datetime import date, datetime

from pydantic import EmailStr, Field, model_validator
from typing_extensions import Literal, Self

from application.schemas.base_schemas import BaseModel, Id, UserBaseS
from application.schemas.order_schemas import ReturnOrderS


class RegisterUserS(UserBaseS):
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)
    gender: Literal["male", "female"]

    @model_validator(mode="after")
    def check_password_match(self) -> Self:
        if (self.password is not None and self.confirm_password is not None
                and self.password != self.confirm_password):
            raise ValueError(
                "Passwords do not match"
            )
        return self


class LoginUserS(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UpdateUserS(UserBaseS):
    role_name: str


class UpdatePartiallyUserS(BaseModel):
    first_name: str = Field(default=None, min_length=2)
    last_name: str = Field(default=None, min_length=2)
    gender: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    registration_date: datetime = None
    role_name: str | None = None
    date_of_birth: date = None


class ReturnUserS(UserBaseS, Id):
    gender: Literal["male", "female"]
    role_name: str


class ReturnUserWithOrdersS(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    orders: list[ReturnOrderS]


class AuthenticatedUserS(UserBaseS, Id):
    role_name: str
