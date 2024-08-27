from uuid import UUID
from pydantic import BaseModel
from application.schemas.order_schemas import AssocBookS


class ReturnCartS(BaseModel):
    cart_id: UUID
    books: list[AssocBookS]


class AddBookToCartS(BaseModel):
    book_id: UUID | str | int
    quantity: int


class CartSessionId(BaseModel):
    session_id: UUID

class DeleteBookFromCartS(BaseModel):
    book_id: UUID

