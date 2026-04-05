from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.postgres import db_client

from ..repositories.book_order_assoc_repo import (
    BookOrderAssocRepository,
    CombinedBookOrderAssocRepoInterface,
)
from ..repositories.book_repo import BookRepository, CombinedBookRepoInterface
from ..repositories.cart_repo import CartRepository, CombinedCartRepositoryInterface
from ..repositories.order_repo import OrderRepository, CombinedOrderRepositoryInterface
from ..repositories.payment_detail_repo import (
    CombinedPaymentDetailRepoInterface,
    PaymentDetailRepository,
)
from ..repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
    ShoppingSessionRepository,
)
from ..services.book_service import BookService
from ..services.cart_service.cart_service import CartService
from ..services.order_service.order_service import OrderService
from ..services.shopping_session_service import ShoppingSessionService
from ..services.user_service import UserService
from .book import get_book_service
from .cart import get_cart_service
from .shopping_session import get_shopping_session_service
from .user import get_user_service


@dataclass(slots=True)
class SqlAlchemyUnitOfWork:
    session: AsyncSession

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.session.rollback()

    def add(self, obj, orm_model) -> None:
        self.session.add(obj)

    async def update(self, orm_model, obj) -> None:
        self.session.add(obj)

    async def commit(self) -> None:
        await self.session.commit()


def get_uow(
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session=session)


def get_order_service(
    order_repo: Annotated[CombinedOrderRepositoryInterface, Depends(OrderRepository)],
    book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
    book_order_assoc_repo: Annotated[
        CombinedBookOrderAssocRepoInterface, Depends(BookOrderAssocRepository)
    ],
    shopping_session_repo: Annotated[
        CombinedShoppingSessionRepositoryInterface, Depends(ShoppingSessionRepository)
    ],
    cart_repo: Annotated[CombinedCartRepositoryInterface, Depends(CartRepository)],
    payment_detail_repo: Annotated[
        CombinedPaymentDetailRepoInterface, Depends(PaymentDetailRepository)
    ],
    book_service: Annotated[BookService, Depends(get_book_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    cart_service: Annotated[CartService, Depends(get_cart_service)],
    shopping_session_service: Annotated[
        ShoppingSessionService, Depends(get_shopping_session_service)
    ],
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_uow)],
) -> OrderService:
    return OrderService(
        order_repo=order_repo,
        book_repo=book_repo,
        book_order_assoc_repo=book_order_assoc_repo,
        shopping_session_repo=shopping_session_repo,
        cart_repo=cart_repo,
        payment_detail_repo=payment_detail_repo,
        book_service=book_service,
        user_service=user_service,
        cart_service=cart_service,
        shopping_session_service=shopping_session_service,
        uow=uow,
    )
