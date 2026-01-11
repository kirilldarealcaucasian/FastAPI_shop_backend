from application.models import CartItem
from application.schemas import ReturnCartS
from application.schemas.order_schemas import AssocBookS


def cart_assembler(cart_items: list[CartItem]) -> ReturnCartS | None:
    """Walks through cart_items, retrieves books and adds them to ReturnCartS"""

    if len(cart_items) == 0:
        return None

    books: list[AssocBookS] = []
    for cart_item in cart_items:  # creates AssocBookS and adds it to books list
        authors = [
            " ".join([author.name]) for author in cart_item.book.authors
        ]  # concatenates first_name with last_name
        categories = [
            category.name for category in cart_item.book.categories
        ]  # creates a list of categories

        books.append(
            AssocBookS(
                book_id=cart_item.book.id,
                book_title=cart_item.book.name,
                authors=authors,
                categories=categories,
                rating=cart_item.book.rating,
                discount=cart_item.book.discount,
                count_ordered=cart_item.quantity,
                price_per_unit=cart_item.book.price_per_unit,
            )
        )

    return ReturnCartS(books=books, cart_id=cart_items[0].session_id)
