import asyncio
import aiohttp
from dataclasses import dataclass
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Book, PaymentDetail, ShoppingSession
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
from ..schemas.response.user import GetUserResponse
from .entity_base_service import EntityBaseService
from ..settings import settings
from shared_lib.exceptions import (
    DBError,
    EntityDoesNotExist,
    NotFoundError,
    ServerError,
)
from ..exceptions import PaymentObjectCreationError
from infrastructure.payment.yookassa.app import (
    PaymentProviderInterface,
)

type ConfirmationURL = str


@dataclass(slots=True, frozen=True)
class PaymentService(EntityBaseService[PaymentDetail]):
    payment_provider: PaymentProviderInterface
    shopping_session_repo: CombinedShoppingSessionRepositoryInterface
    cart_repo: CombinedCartRepositoryInterface
    payment_detail_repo: CombinedPaymentDetailRepoInterface

    async def get_payment_by_id(
        self, session: AsyncSession, payment_id: UUID
    ) -> PaymentDetail:
        try:
            return await self.payment_detail_repo.get_by_id(
                session=session, id=payment_id
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="PaymentDetail")
        except DBError:
            raise ServerError()

    async def make_payment(
        self, session: AsyncSession, shopping_session_id: UUID
    ) -> ConfirmationURL:
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

        if shopping_session.user_id is None:
            raise EntityDoesNotExist(entity="User")
        user = await self._get_user_from_auth_service(user_id=shopping_session.user_id)
        cart_owner_full_name = f"{user.first_name} {user.last_name}"

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
            customer_email=user.email,
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

        session.add(orm_model)
        await super().commit(session=session)

        logger.debug("Starting to check payment status . . .")
        asyncio.create_task(
            self.payment_provider.check_payment_status(
                shopping_session_id=shopping_session_id,
                payment_id=payment_creds.payment_id,
                amount=shopping_session.total,
            )
        )  # schedule a task to the event loop so that it could execute in the "background"

        return payment_creds.confirmation_url

    async def _get_user_from_auth_service(self, user_id: int) -> GetUserResponse:
        timeout = aiohttp.ClientTimeout(total=settings.AUTH_SERVICE_TIMEOUT_SECONDS)
        url = f"{settings.AUTH_SERVICE_BASE_URL}/users/{user_id}"

        try:
            async with aiohttp.ClientSession(timeout=timeout) as http:
                async with http.get(url) as response:
                    if response.status == 404:
                        raise EntityDoesNotExist(entity="User")
                    if response.status >= 400:
                        raise ServerError("failed to retrieve user from auth service")

                    payload = await response.json()
        except aiohttp.ClientError as exc:
            logger.opt(exception=exc).error("failed to call auth service")
            raise ServerError("auth service is unavailable")

        return GetUserResponse.model_validate(payload)
