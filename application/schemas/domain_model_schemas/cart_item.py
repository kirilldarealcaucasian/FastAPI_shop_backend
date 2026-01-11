from uuid import UUID

from pydantic import BaseModel


class CartItemS(BaseModel):
    session_id: UUID
    book_id: int
    quantity: int
