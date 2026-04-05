from uuid import UUID

from pydantic import BaseModel

from .order import AssocBookResponse


class GetCartResponse(BaseModel):
    cart_id: UUID | str
    books: list[AssocBookResponse]


class CartSessionIdResponse(BaseModel):
    session_id: UUID
