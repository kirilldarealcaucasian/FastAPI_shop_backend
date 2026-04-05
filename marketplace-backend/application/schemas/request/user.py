from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, model_validator
from typing_extensions import Literal, Self

from ..base_schemas import UserBaseS


class RegisterUserRequest(UserBaseS):
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)
    gender: Literal["male", "female"]

    @model_validator(mode="after")
    def check_password_match(self) -> Self:
        if (
            self.password is not None
            and self.confirm_password is not None
            and self.password != self.confirm_password
        ):
            raise ValueError("Passwords do not match")
        return self


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UpdateUserRequest(UserBaseS):
    role_name: str


class UpdatePartiallyUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    registration_date: datetime | None = None
    role_name: str | None = None
    date_of_birth: date | None = None
