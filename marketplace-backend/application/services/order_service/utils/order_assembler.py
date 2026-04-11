from collections.abc import Sequence

from ....models import Book, BookOrderAssoc
from ....schemas.response.order import AssocBookResponse


def order_assembler(
    order_details: Sequence[BookOrderAssoc],
) -> Sequence[AssocBookResponse]:
    """Walks through order_details, retrieves books and adds them to GetOrderResponse"""

    books: list[AssocBookResponse] = []

    for order_detail in order_details:
        book: Book = order_detail.book
        authors: list[str] = [author.name for author in book.authors]

        categories: list[str] = [
            category.name for category in book.categories
        ]

        books.append(
            AssocBookResponse(
                book_id=book.id,
                book_title=book.name,
                authors=authors,
                categories=categories,
                rating=book.rating,
                discount=book.discount,
                count_ordered=order_detail.count_ordered,
                price_per_unit=book.price_per_unit,
            )
        )

    return books
