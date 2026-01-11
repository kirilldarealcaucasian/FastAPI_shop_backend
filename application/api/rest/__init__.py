__all__ = (
    "image_router",
    "order_router",
    "book_router",
    "user_router",
    "author_router",
    "publisher_router",
    "cart_router",
    "checkout_router"
)

from .v1 import (author_router, book_router, cart_router, checkout_router,
                 image_router, order_router, publisher_router, user_router)
