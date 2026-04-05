from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing_extensions import Literal

from ...types import Id
from .order import GetOrderResponse


class UserBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: EmailStr


class GetUserResponse(UserBaseResponse):
    id: Id
    gender: Literal["male", "female"]
    role_name: str


class GetUserWithOrdersResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    orders: list[GetOrderResponse]


class AuthenticatedUserResponse(UserBaseResponse):
    id: Id
    role_name: str
