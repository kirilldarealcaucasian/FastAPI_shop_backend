from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from application.schemas.domain_model_schemas.book import BookS
from application.schemas.domain_model_schemas.shopping_session import ShoppingSessionS
from core.exceptions import DeleteBooksFromCartError, AddBooksToCartError


class CartItemS(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID | None = None
    book_id: UUID | None = None
    quantity: int | None = Field(default=None, gt=0)

    def remove_books_from_cart(
            self,
            quantity,
            book: BookS,
            shopping_session: ShoppingSessionS
    ):
        if self.quantity - quantity < 0:
            raise DeleteBooksFromCartError(
                info="You're trying to delete more books that there exists in the cart"
            )
        self.quantity -= quantity
        book.number_in_stock += quantity
        shopping_session.total -= book.price_with_discount

    def put_books_in_cart(
            self,
            quantity: int,
            book: BookS,
            shopping_session: ShoppingSessionS
    ):
        if book.number_in_stock - quantity < 0:
            raise AddBooksToCartError(
                info="You're trying to add more books that there are in stock"
            )
        print("QUANTITY DO IN put_books_in_cart: ", self.quantity)
        self.quantity += quantity
        book.number_in_stock -= quantity
        shopping_session.total += book.price_with_discount




