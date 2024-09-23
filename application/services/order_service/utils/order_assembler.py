from application.models import BookOrderAssoc, Book
from application.schemas.order_schemas import AssocBookS


def order_assembler(order_details: list[BookOrderAssoc]) -> list[AssocBookS]:
    """Walks through order_details, retrieves books and adds them to ReturnOrderS"""

    books: list[AssocBookS] = []

    for order_detail in order_details:
        book: Book = order_detail.book
        authors: list[str] = [
            " ".join([author.first_name, author.last_name]
                     )
            for author in book.authors
        ]  # concat authors' first and last name

        categories: list[str] = [
            category.name for category in book.categories
        ]

        books.append(
            AssocBookS(
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