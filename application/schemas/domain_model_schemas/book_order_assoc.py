from uuid import UUID

from pydantic import BaseModel, Field

from .book import BookS
from .order import OrderS

from core.exceptions import AddBooksToCartError, DeleteBooksFromCartError


class BookOrderAssocS(BaseModel):
    order_id: int | None = None
    book_id: UUID | None = None
    count_ordered: int | None = Field(default=0, ge=1)

    def remove_books_from_cart(
            self,
            quantity,
            book: BookS,
            order: OrderS
    ):
        if self.quantity - quantity < 0:
            raise DeleteBooksFromCartError(
                info="You're trying to delete more books that there exists in the order"
            )
        self.count_ordered -= quantity
        book.number_in_stock += quantity
        order.total_sum -= book.price_with_discount

    def put_books_in_order(
            self,
            quantity: int,
            book: BookS,
            order: OrderS
    ):
        if book.number_in_stock - quantity < 0:
            raise AddBooksToCartError(
                info="You're trying to add more books that there are in stock"
            )
        print("count_ordered before: ", self.count_ordered)
        self.count_ordered += quantity
        print("count_ordered after: ", self.count_ordered)
        book.number_in_stock -= quantity
        order.total_sum += book.price_with_discount
