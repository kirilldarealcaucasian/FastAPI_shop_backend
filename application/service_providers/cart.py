from typing import Annotated
from fastapi import Depends

from ..repositories.book_repo import CombinedBookRepoInterface, BookRepository
from ..repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from ..services.user_service import UserService
from ..services.cart_service.cart_service import CartService
from ..services.shopping_session_service import ShoppingSessionService
from ..services.book_service import BookService
from .shopping_session import get_shopping_session_service
from .book import get_book_service
from .user import get_user_service
from infrastructure.redis import redis_client


def get_cart_service(
    book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
    cart_repo: Annotated[CombinedCartRepositoryInterface, Depends(CartRepository)],
    shopping_session_service: Annotated[
        ShoppingSessionService, Depends(get_shopping_session_service)
    ],
    user_service: Annotated[UserService, Depends(get_user_service)],
    book_service: Annotated[BookService, Depends(get_book_service)],
) -> CartService:
    return CartService(
        book_repo=book_repo,
        cart_repo=cart_repo,
        shopping_session_service=shopping_session_service,
        user_service=user_service,
        book_service=book_service,
        redis_con=redis_client.connection,
    )
