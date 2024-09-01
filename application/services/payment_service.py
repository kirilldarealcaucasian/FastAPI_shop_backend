import asyncio
import uuid
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application import User, Book
from application.models import ShoppingSession, CartItem
from application.repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from application.repositories.payment_detail_repo import CombinedPaymentDetailRepoInterface, PaymentDetailRepository
from application.repositories.shopping_session_repo import CombinedShoppingSessionRepositoryInterface, \
    ShoppingSessionRepository
from application.schemas import OrderItemS, CreatePaymentS, ReturnPaymentS
from application.schemas.domain_model_schemas import PaymentDetailS
from core import EntityBaseService
from core.exceptions import EntityDoesNotExist, PaymentObjectCreationError, ServerError
from infrastructure.payment.yookassa.app import (
    PaymentProviderInterface, YooKassaPaymentProvider
)
from logger import logger


ConfirmationURL = TypeAlias = str


class PaymentService(EntityBaseService):

    def __init__(
            self,
            payment_provider: Annotated[
                PaymentProviderInterface, Depends(YooKassaPaymentProvider)],
            shopping_session_repo: Annotated[
                CombinedShoppingSessionRepositoryInterface, Depends(ShoppingSessionRepository)
            ],
            cart_repo: Annotated[
                CombinedCartRepositoryInterface, Depends(CartRepository)
            ],
            payment_detail_repo: Annotated[
                CombinedPaymentDetailRepoInterface, Depends(PaymentDetailRepository)
            ]
    ):
        self.payment_provider = payment_provider
        super().__init__(
            shopping_session_repo=shopping_session_repo,
            cart_repo=cart_repo,
            payment_detail_repo=payment_detail_repo
        )
        self.shopping_session_repo = shopping_session_repo
        self.cart_repo = cart_repo
        self.payment_detail_repo = payment_detail_repo

    async def make_payment(
            self,
            session: AsyncSession,
            shopping_session_id: UUID
    ) -> ConfirmationURL:
        """
        Retrieves cart items and information about the cart (ShoppingSession),
        creates PaymentDetail object, then calls to payment provider to get
        payment url and starts polling
        asynchronously for payment status in the background
        """
        shopping_session: ShoppingSession = await self.shopping_session_repo.get_by_id(
            session=session,
            id=shopping_session_id
        )

        cart: list[CartItem] = await self.cart_repo.get_cart_by_session_id(
            session=session,
            cart_session_id=shopping_session_id
        )

        if shopping_session is None:
            logger.info(
                "ShoppingSession does not exist",
                extra={"shopping_session_id", shopping_session_id}
            )
            raise EntityDoesNotExist(
                entity="Cart"
            )

        cart_owner: User = shopping_session.user
        cart_owner_full_name = " ".join([cart_owner.first_name, cart_owner.last_name])

        order_items: list[OrderItemS] = []

        for item in cart:
            book: Book = item.book
            order_items.append(
                OrderItemS(
                    book_name=book.name,
                    quantity=item.quantity,
                    price=book.price_with_discount
                )
            )

        order_item_names = ", ".join([order_item.book_name for order_item in order_items])
        description = f"You're ordering: {order_item_names}"

        payment_data = CreatePaymentS(
            customer_full_name=cart_owner_full_name,
            customer_email=cart_owner.email,
            total_amount=shopping_session.total,
            currency="RUB",
            description=description,
            items=order_items
        )

        try:
            payment_creds: ReturnPaymentS = self.payment_provider.create_payment(
                payment_data=payment_data
            )
        except PaymentObjectCreationError:
            raise ServerError("Something went wrong during payment process")

        payment_id: UUID = uuid.UUID(payment_creds.payment_id)

        domain_model = PaymentDetailS(
            id=payment_id,
            status="pending",
            payment_provider="yookassa",
            amount=shopping_session.total
        )

        _ = await super().create(
            session=session,
            repo=self.payment_detail_repo,
            domain_model=domain_model
        )  # create PaymentDetail, if sth is wrong http_exception is raised

        logger.debug("Starting to check payment status . . .")
        _ = asyncio.create_task(self.payment_provider.check_payment_status(
            shopping_session_id=shopping_session_id,
            payment_id=payment_creds.payment_id)
        )  # schedule a task to the event loop so that it could execute in the "background"

        return payment_creds.confirmation_url

