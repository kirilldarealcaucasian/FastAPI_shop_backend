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

from application.api.rest.v1.routers.image_routers import router as image_router
from application.api.rest.v1.routers.order_routers import router as order_router
from application.api.rest.v1.routers.book_routers import router as book_router
from application.api.rest.v1.routers.user_routers import router as user_router
from application.api.rest.v1.routers.author_routers import router as author_router
from application.api.rest.v1.routers.publisher_routers import router as publisher_router
from application.api.rest.v1.routers.cart_routers import router as cart_router
from application.api.rest.v1.routers.checkout_routers import router as checkout_router
