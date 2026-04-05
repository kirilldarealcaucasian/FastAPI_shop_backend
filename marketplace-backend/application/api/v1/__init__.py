__all__ = (
    "order_router",
    "book_router",
    "user_router",
    "author_router",
    "cart_router",
    "payment_router",
)

from .routers.author import router as author_router
from .routers.book import router as book_router
from .routers.payment import router as payment_router
from .routers.order import router as order_router
from .routers.user import router as user_router
from .routers.cart import router as cart_router
