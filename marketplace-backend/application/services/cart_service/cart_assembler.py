from ...models import CartItem
from ...schemas.response.cart import GetCartResponse
from ...schemas.response.order import AssocBookResponse


def assemble_cart(cart_items: list[CartItem]) -> GetCartResponse | None:
    """Walks through cart_items, retrieves books and adds them to GetCartResponse"""

    if len(cart_items) == 0:
        return None

    books: list[AssocBookResponse] = []
    for cart_item in cart_items:  # creates AssocBookResponse and adds it to books list
        authors = [
            " ".join([author.name]) for author in cart_item.book.authors
        ]  # concatenates first_name with last_name
        categories = [
            category.name for category in cart_item.book.categories
        ]  # creates a list of categories

        books.append(
            AssocBookResponse(
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

    return GetCartResponse(books=books, cart_id=cart_items[0].session_id)
