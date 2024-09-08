from uuid import UUID
from pydantic import BaseModel, Field
from application.schemas.order_schemas import AssocBookS


class ReturnCartS(BaseModel):
    cart_id: UUID | str
    books: list[AssocBookS]


class AddBookToCartS(BaseModel):
    book_id: UUID | str | int
    quantity: int


class CartSessionId(BaseModel):
    session_id: UUID


class DeleteBookFromCartS(BaseModel):
    book_id: UUID
    quantity: int = Field(default=1, ge=1)


class CartPrimaryIdentifier(BaseModel):
    book_id: UUID
    session_id: UUID
