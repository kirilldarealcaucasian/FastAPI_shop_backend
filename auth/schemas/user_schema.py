from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from typing_extensions import Literal, Self

RoleName = Literal["user", "manager", "admin"]


class RegisterUserRequest(BaseModel):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)
    gender: Literal["male", "female"]
    date_of_birth: date | None = None

    @model_validator(mode="after")
    def check_password_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class GetUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    gender: Literal["male", "female"]
    role_name: RoleName


class AuthenticatedUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role_name: RoleName


class AssignRoleRequest(BaseModel):
    role_name: RoleName


class UpdateUserRequest(BaseModel):
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: EmailStr
    role_name: RoleName


class UpdatePartiallyUserRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=2)
    last_name: str | None = Field(default=None, min_length=2)
    gender: Literal["male", "female"] | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    role_name: RoleName | None = None
    date_of_birth: date | None = None
