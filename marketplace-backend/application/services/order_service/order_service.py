from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Book, BookOrderAssoc, Order
from ...models.order_status import OrderStatus
from ...repositories.book_order_assoc_repo import (
    CombinedBookOrderAssocRepoInterface,
)
from ...repositories.book_repo import CombinedBookRepoInterface
from ...repositories.cart_repo import (
    CombinedCartRepositoryInterface,
)
from ...repositories.order_repo import (
    CombinedOrderRepositoryInterface,
)
from ...repositories.payment_detail_repo import (
    CombinedPaymentDetailRepoInterface,
)
from ...repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
)
from ...schemas.request.order import (
    CreateOrderRequest,
    UpdatePartiallyOrderRequest,
    AddBookToOrderRequest,
)
from ...schemas.response.order import (
    GetOrderResponse,
    AssocBookResponse,
    OrderIdResponse,
    GetShortOrderResponse,
)
from ...schemas.response.cart import GetCartResponse
from ...schemas.response.shopping_session import GetShoppingSessionResponse
from ...schemas.filters import PaginationS
from ...services.book_service import BookService
from ...services.cart_service.cart_service import CartService
from ...services.shopping_session_service import ShoppingSessionService
from ...services.user_service import UserService
from ...services.order_service.utils import order_assembler
from ...filters import Pagination
from ...types import BookOrderPrimaryIdentifier
from ..entity_base_service import EntityBaseService
from shared_lib.exceptions import (
    BadRequest,
    DBError,
    EntityDoesNotExist,
    NotFoundError,
    ServerError,
)
from ...exceptions import PaymentFailedError
from infrastructure.postgres import db_client

OrderId: TypeAlias = int
books_data: TypeAlias = str


@dataclass(slots=True)
class OrderService(EntityBaseService[Order]):
    order_repo: CombinedOrderRepositoryInterface
    book_repo: CombinedBookRepoInterface
    book_order_assoc_repo: CombinedBookOrderAssocRepoInterface
    shopping_session_repo: CombinedShoppingSessionRepositoryInterface
    cart_repo: CombinedCartRepositoryInterface
    payment_detail_repo: CombinedPaymentDetailRepoInterface
    book_service: BookService
    user_service: UserService
    cart_service: CartService
    shopping_session_service: ShoppingSessionService
    uow: Any

    async def create_order(
        self, session: AsyncSession, dto: CreateOrderRequest
    ) -> OrderIdResponse:
        data: dict = dto.model_dump(exclude_unset=True)

        _ = await self.user_service.get_user_by_id(
            session=session, id=data["user_id"]
        )  # if no exception was raised

        created_order = await self.order_repo.create(
            session=session, orm_model=Order(**data)
        )

        return OrderIdResponse(id=created_order.id)

    async def get_all_orders(
        self, session: AsyncSession, pagination: PaginationS
    ) -> Sequence[GetShortOrderResponse]:
        orders = await self.order_repo.get_all_orders(
            session=session,
            pagination=Pagination(
                limit=pagination.limit,
                page=pagination.page,
            ),
        )

        res: list[GetShortOrderResponse] = []

        for order in orders:
            order_owner_full_name = getattr(order.user, "name", "")
            res.append(
                GetShortOrderResponse(
                    owner_name=order_owner_full_name,
                    owner_email=order.user.email,
                    order_id=order.id,
                    order_status=order.order_status,
                    total_sum=float(order.total_sum),
                    order_date=order.order_date,
                )
            )
        return res

    async def get_order_by_id(
        self, session: AsyncSession, order_id: int
    ) -> GetOrderResponse:

        exists: bool = await self.order_repo.check_if_order_exists(
            session=session, order_id=order_id
        )

        if not exists:
            raise EntityDoesNotExist(
                entity="Order",
            )

        try:
            order_details: Sequence[BookOrderAssoc] = await self.order_repo.get_by_id(
                session=session, id=order_id
            )
        except EntityDoesNotExist:
            return GetOrderResponse(order_id=order_id, books=[])

        books = order_assembler(order_details)

        return GetOrderResponse(order_id=order_id, books=books)

    async def get_orders_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> Sequence[GetOrderResponse]:
        order_details: Sequence[BookOrderAssoc] = []

        try:
            order_details = await self.order_repo.get_orders_by_user_id(
                session=session, user_id=user_id
            )  # details of orders made by a user
            logger.debug(
                "order_details in get_order_by_id",
                extra={"order_details": order_details},
            )
        except (NotFoundError, DBError) as e:
            if type(e) is NotFoundError:
                logger.info(f"{e.entity} not found", exc_info=True)
                raise EntityDoesNotExist(e.entity)
            if type(e) is DBError:
                logger.error("DB error", exc_info=True)
                raise ServerError()

        orders: dict[OrderId, list[BookOrderAssoc]] = defaultdict(list)

        for order_detail in order_details:
            # arrange order details by order_ids
            orders[order_detail.order_id].append(order_detail)

        result_orders: list[GetOrderResponse] = []

        for order_id, details in orders.items():
            # for each order convert it into GetOrderResponse
            books = order_assembler(order_details=details)
            result_orders.append(GetOrderResponse(order_id=order_id, books=books))

        return result_orders

    async def get_order_details_by_payment_id(
        self, session: AsyncSession, payment_id: UUID
    ) -> GetOrderResponse:
        try:
            order: Order = await self.order_repo.get_order_by_payment_id(
                session=session, payment_id=payment_id
            )
        except (NotFoundError, DBError) as e:
            if type(e) is NotFoundError:
                raise EntityDoesNotExist(entity=e.entity)
            logger.error("failed to get payment by id", exc_info=True)
            raise ServerError()

        order_details: list[BookOrderAssoc] = order.order_details

        books = order_assembler(order_details)

        return GetOrderResponse(order_id=order.id, books=books)

    async def get_order_summary(self, session: AsyncSession, payment_id: UUID) -> Order:
        try:
            order: Order = await self.order_repo.get_order_summary(
                session=session, payment_id=payment_id
            )
            return order
        except (NotFoundError, DBError) as e:
            if type(e) is NotFoundError:
                raise EntityDoesNotExist(entity=e.entity)
            logger.error("failed to get payment by id", exc_info=True)
            raise ServerError()

    async def delete_order(self, session: AsyncSession, order_id: int) -> None:
        exists: bool = await self.order_repo.check_if_order_exists(
            session=session, order_id=order_id
        )
        if not exists:
            raise EntityDoesNotExist(entity="Order")

        await super(OrderService, self).delete(
            repo=self.order_repo, session=session, instance_id=order_id
        )

        await super(OrderService, self).commit(session=session)

    async def update_order(
        self,
        session: AsyncSession,
        order_id: int,
        dto: UpdatePartiallyOrderRequest,
    ):
        dto_data: dict = dto.model_dump(exclude_none=True, exclude_unset=True)
        orders = await self.order_repo.get_all(session=session, id=order_id)
        if not orders:
            raise EntityDoesNotExist(entity="Order")

        order: Order = orders[0]
        for key, value in dto_data.items():
            setattr(order, key, value)

        return await self.order_repo.update(
            orm_model=order,
            instance_id=order_id,
            session=session,
        )

    async def add_book_to_order(
        self, order_id: int, session: AsyncSession, dto: AddBookToOrderRequest
    ) -> GetOrderResponse:
        book: Book | None = await self.book_repo.get_by_id(
            session=session, id=dto.book_id
        )  # if no book http_exception will be raised

        if not book:
            raise EntityDoesNotExist(entity="Book")

        if book.number_in_stock - dto.count_ordered < 0:
            raise BadRequest(
                detail=f"You're trying to order too many books, only {book.number_in_stock} left in stock"
            )

        order_item: BookOrderAssoc | None = await self.book_order_assoc_repo.get_by_id(
            session=session,
            id=BookOrderPrimaryIdentifier(order_id=order_id, book_id=book.id),
        )

        if order_item is None:
            order_item = BookOrderAssoc(
                book_id=book.id,
                order_id=order_id,
                count_ordered=0,
            )
            await self.book_order_assoc_repo.create(
                session=session,
                orm_model=order_item,
            )
            session.expire_all()
            order_item = await self.book_order_assoc_repo.get_by_id(
                session=session,
                id=BookOrderPrimaryIdentifier(book_id=book.id, order_id=order_id),
            )

        if order_item is None:
            raise ServerError("failed to create order item")

        order: Order = order_item.order
        if order is None:
            raise EntityDoesNotExist(entity="Order")

        order_item.count_ordered += dto.count_ordered
        book.number_in_stock -= dto.count_ordered
        order.total_sum += book.price_with_discount * dto.count_ordered

        async with self.uow as uow:
            await uow.update(orm_model=BookOrderAssoc, obj=order_item)
            await uow.update(orm_model=Book, obj=book)
            await uow.update(orm_model=Order, obj=order)
            await uow.commit()

        session.expire_all()
        updated_order: GetOrderResponse = await self.get_order_by_id(
            session=session, order_id=order_id
        )

        return updated_order

    async def delete_book_from_order(
        self,
        session: AsyncSession,
        book_id: UUID,
        order_id: int,
    ) -> GetOrderResponse:
        try:
            _ = await self.order_repo.get_by_id(
                session=session,
                id=order_id,
            )
        except EntityDoesNotExist:
            raise EntityDoesNotExist("Book (in the order)")

        try:
            await self.order_repo.delete_book_from_order_by_id(
                session=session, book_id=book_id, order_id=order_id
            )
            return await self.get_order_by_id(session=session, order_id=order_id)
        except DBError:
            extra = {"book_id": book_id, "order_id": order_id}
            logger.error("Failed to delete_book from order", exc_info=True, extra=extra)
            raise ServerError()

    async def perform_order(
        self,
        payment_id: UUID,
        shopping_session_id: UUID,
        status: Literal["success", "failed"],
    ):
        """If status is "success" -> transactionally update payment status
        and create order with status done. Then copy books from cart
        to order details, updating order total sum. After, delete the cart"""
        if db_client.async_session is None:
            raise ServerError("DB session is unavailable")

        async with db_client.async_session() as session:
            try:
                payment_details = await self.payment_detail_repo.get_by_id(
                    session=session, id=payment_id
                )
            except (NotFoundError, DBError) as e:
                if isinstance(e, NotFoundError):
                    raise EntityDoesNotExist("Payment object")
                raise ServerError("failed to create order")
            if payment_details is None:
                raise EntityDoesNotExist("Payment object")

            if status == "success":
                logger.debug("payment status is successful")
                cart: GetCartResponse = await self.cart_service.get_cart_by_session_id(
                    session=session, shopping_session_id=shopping_session_id
                )

                shopping_session: GetShoppingSessionResponse = (
                    await self.shopping_session_service.get_shopping_session_by_id(
                        session=session, id=shopping_session_id
                    )
                )
                try:
                    payment_details.status = "success"
                    cart_books: list[AssocBookResponse] = list(cart.books)

                    order_orm_models: list[BookOrderAssoc] = []
                    order_create_obj = Order(
                        user_id=shopping_session.user_id,
                        order_status=OrderStatus.DONE,
                        payment_id=payment_id,
                        total_sum=payment_details.amount,
                    )  # create order obj
                    session.add(payment_details)
                    session.add(order_create_obj)
                    await super(OrderService, self).commit(session=session)
                except ServerError:
                    extra = {
                        "payment_id": payment_id,
                        "shopping_session_id": shopping_session_id,
                        "payment_status": "success",
                    }
                    logger.error(
                        "Failed to change payment status to 'success' or create order or both",
                        extra=extra,
                    )
                    raise PaymentFailedError(
                        detail="Failed to create order. Refund is coming soon."
                    )

                order: Order = await self.order_repo.get_order_by_payment_id(
                    session=session, payment_id=payment_id
                )  # retrieve previously created order

                for book in cart_books:  # prepare books to be copied from cart to order
                    order_orm_models.append(
                        BookOrderAssoc(
                            book_id=book.book_id,
                            order_id=order.id,
                            count_ordered=book.count_ordered,
                        )
                    )

                try:
                    await self.book_order_assoc_repo.create_many(
                        session=session, orm_models=order_orm_models
                    )  # copy books from cart to order
                    await super(OrderService, self).commit(session=session)
                    logger.info("order has been created and filled successfully")
                except (ServerError, DBError):
                    order.order_status = OrderStatus.REFUND
                    session.add(order)
                    await super(OrderService, self).commit(session=session)
                    extra = {
                        "payment_id": payment_id,
                        "shopping_session_id": shopping_session_id,
                        "order_domain_models": order_orm_models,
                    }
                    logger.error(
                        "failed to copy books from cart to order",
                        exc_info=True,
                        extra=extra,
                    )
                    raise PaymentFailedError(
                        detail="Failed to create order. Refund is coming soon."
                    )

                try:
                    await self.shopping_session_service.delete(
                        session=session,
                        repo=self.shopping_session_repo,
                        instance_id=shopping_session_id,
                    )  # delete cart with its items
                    await super(OrderService, self).commit(session=session)
                except DBError:
                    extra = {"shopping_session_id": shopping_session_id}
                    logger.error("failed to delete cart", extra=extra)

            else:
                logger.debug("payment status is 'failed'")
                payment_details.status = "failed"
                session.add(payment_details)
                await super(OrderService, self).commit(
                    session=session
                )  # update payment status to failed
                raise PaymentFailedError(detail="Payment was failed.")
