import asyncio
from dataclasses import dataclass
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Book, PaymentDetail, ShoppingSession, User
from ..repositories.cart_repo import (
    CombinedCartRepositoryInterface,
)
from ..repositories.payment_detail_repo import (
    CombinedPaymentDetailRepoInterface,
)
from ..repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
)
from ..schemas.request.order import OrderItemRequest
from ..schemas.request.payment import CreatePaymentRequest
from ..schemas.response.payment import CreatePaymentResponse
from .entity_base_service import EntityBaseService
from ..exceptions import EntityDoesNotExist, PaymentObjectCreationError, ServerError
from infrastructure.payment.yookassa.app import (
    PaymentProviderInterface,
)

type ConfirmationURL = str


@dataclass(slots=True, frozen=True)
class PaymentService(EntityBaseService):
    payment_provider: PaymentProviderInterface
    shopping_session_repo: CombinedShoppingSessionRepositoryInterface
    cart_repo: CombinedCartRepositoryInterface
    payment_detail_repo: CombinedPaymentDetailRepoInterface

    async def get_payment_by_id(
        self, session: AsyncSession, payment_id: UUID
    ) -> PaymentDetail:
        payment: PaymentDetail = await super().get_by_id(
            repo=self.payment_detail_repo, session=session, id=payment_id
        )
        return payment

    async def make_payment(self, session: AsyncSession, shopping_session_id: UUID):
        """
        Retrieves cart items and information about the cart (ShoppingSession),
        creates PaymentDetail object, then calls to payment provider to get
        payment url and starts polling
        asynchronously for payment status in the background
        """
        shopping_session: ShoppingSession | None = (
            await self.shopping_session_repo.get_by_id(
                session=session, id=shopping_session_id
            )
        )

        if not shopping_session:
            raise EntityDoesNotExist(entity="ShoppingSession")

        cart = await self.cart_repo.get_cart_by_session_id(
            session=session, cart_session_id=shopping_session_id
        )

        if shopping_session is None:
            logger.info(
                "ShoppingSession does not exist",
                extra={"shopping_session_id", shopping_session_id},
            )
            raise EntityDoesNotExist(entity="Cart")

        cart_owner: User = shopping_session.user
        cart_owner_full_name = " ".join([cart_owner.first_name, cart_owner.last_name])

        order_items: list[OrderItemRequest] = (
            []
        )  # list of books that are going to be in the order

        for item in cart:
            book: Book = item.book
            order_items.append(
                OrderItemRequest(
                    book_name=book.name,
                    quantity=item.quantity,
                    price=book.price_with_discount,
                )
            )

        order_item_names = ", ".join(
            [order_item.book_name for order_item in order_items]
        )
        description = f"You're ordering: {order_item_names}"

        payment_data = CreatePaymentRequest(
            customer_full_name=cart_owner_full_name,
            customer_email=cart_owner.email,
            total_amount=shopping_session.total,
            currency="RUB",
            description=description,
            items=order_items,
        )

        try:
            payment_creds: CreatePaymentResponse = self.payment_provider.create_payment(
                payment_data=payment_data,
            )
        except PaymentObjectCreationError:
            raise ServerError(
                """
                Something went wrong during payment process.
                It's impossible to perform payment now. Try later"""
            )

        orm_model = PaymentDetail(
            id=payment_creds.payment_id,
            status="pending",
            payment_provider="yookassa",
            amount=shopping_session.total,
        )

        _ = await super().create(
            repo=self.payment_detail_repo, session=session, orm_model=orm_model
        )  # create PaymentDetail, if sth is wrong http_exception is raised

        logger.debug("Starting to check payment status . . .")
        _ = asyncio.create_task(
            self.payment_provider.check_payment_status(
                shopping_session_id=shopping_session_id,
                payment_id=payment_creds.payment_id,
                amount=shopping_session.total,
            )
        )  # schedule a task to the event loop so that it could execute in the "background"

        return payment_creds.confirmation_url
