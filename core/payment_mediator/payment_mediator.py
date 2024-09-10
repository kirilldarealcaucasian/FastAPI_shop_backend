from application.repositories import ImageRepository, UserRepository, OrderRepository
from application.repositories.book_order_assoc_repo import BookOrderAssocRepository
from application.services import OrderService, BookService, UserService, CartService, ShoppingSessionService
from core.base_repos import SqlAlchemyUnitOfWork
from core.payment_mediator.payment_events import PaymentEvents
from infrastructure.payment.yookassa.app import YooKassaPaymentProvider

from application.repositories.book_repo import BookRepository
from application.repositories.cart_repo import CartRepository
from application.repositories.payment_detail_repo import PaymentDetailRepository
from application.repositories.shopping_session_repo import ShoppingSessionRepository
from application.services.storage.internal_storage import internal_storage_service


class PaymentMediator:
    def __init__(
            self,
            order_service: OrderService,
            payment_provider: YooKassaPaymentProvider,
    ):
        self._order_service = order_service
        self._order_service.mediator = self

        self._payment_provider = payment_provider
        self._payment_provider.mediator = self

    async def notify(
            self, sender: object,
            event: str, *args, **kwargs
    ):
        if PaymentEvents.PAYMENT_SUCCEEDED.value == event or PaymentEvents.PAYMENT_FAILED:
            await self._order_service.perform_order(
                *args, **kwargs
            )

        elif PaymentEvents.MAKE_REFUND.value == event:
            await self._payment_provider.make_refund(
                *args, **kwargs
            )


book_order_assoc_repo = BookOrderAssocRepository()
book_repo = BookRepository()
shopping_session_repo = ShoppingSessionRepository()
cart_repo = CartRepository()
payment_detail_repo = PaymentDetailRepository()
image_repo = ImageRepository()
user_repo = UserRepository()

book_service = BookService(
    book_repo=book_repo,
    image_repo=image_repo,
    storage=internal_storage_service
)

order_repo = OrderRepository()

user_service = UserService(
    user_repo=user_repo
)

shopping_session_service = ShoppingSessionService(
    shopping_session_repo=shopping_session_repo
)

uow = SqlAlchemyUnitOfWork()

cart_service = CartService(
    book_repo=book_repo,
    cart_repo=cart_repo,
    shopping_session_service=shopping_session_service,
    user_service=user_service,
    book_service=book_service,
    uow=uow
)

order_service = OrderService(
    book_order_assoc_repo=book_order_assoc_repo,
    book_repo=book_repo,
    shopping_session_repo=shopping_session_repo,
    cart_repo=cart_repo,
    payment_detail_repo=payment_detail_repo,
    order_repo=order_repo,
    book_service=book_service,
    user_service=user_service,
    cart_service=cart_service,
    shopping_session_service=shopping_session_service,
    uow=uow
)

payment_provider = YooKassaPaymentProvider()

payment_mediator = PaymentMediator(
    order_service=order_service,
    payment_provider=payment_provider
)
