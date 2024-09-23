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

from .image_routers import router as image_router
from .order_routers import router as order_router
from .book_routers import router as book_router
from .user_routers import router as user_router
from .author_routers import router as author_router
from .publisher_routers import router as publisher_router
from .cart_routers import router as cart_router
from .checkout_routers import router as checkout_router
