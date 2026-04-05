from pydantic import BaseModel, Field


class AddBookToCartRequest(BaseModel):
    book_id: int
    quantity: int


class DeleteBookFromCartRequest(BaseModel):
    book_id: int
    quantity: int = Field(default=1, ge=1)
