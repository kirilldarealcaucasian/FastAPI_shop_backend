from collections import defaultdict
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import Book
from application.repositories.book_order_assoc_repo import BookOrderAssocRepository, CombinedBookOrderAssocRepoInterface
from application.repositories.book_repo import CombinedBookRepoInterface
from application.repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from application.repositories.payment_detail_repo import CombinedPaymentDetailRepoInterface, PaymentDetailRepository
from application.repositories.shopping_session_repo import CombinedShoppingSessionRepositoryInterface
from application.schemas.domain_model_schemas import OrderS, BookOrderAssocS, PaymentDetailS
from application.services.order_service.utils import order_assembler
from core.exceptions import (
    EntityDoesNotExist,
    DomainModelConversionError, NotFoundError,
    DBError, ServerError
)
from application.schemas import (
    ReturnOrderS,
    CreateOrderS,
    BookSummaryS,
    OrderSummaryS,
    ReturnUserS,
    ShortenedReturnOrderS,
    ReturnUserWithOrdersS,
    UpdatePartiallyOrderS, ReturnCartS, ReturnShoppingSessionS,
)

from application.repositories import (
    OrderRepository,
    BookRepository,
    ShoppingSessionRepository
)

from application.schemas.filters import PaginationS
from application.schemas.order_schemas import AssocBookS, AddBookToOrderS, OrderIdS
from application.models import Order, BookOrderAssoc
from typing import Annotated, TypeAlias, Union, Literal

from infrastructure.postgres import db_client
from logger import logger
from application.repositories.order_repo import CombinedOrderRepositoryInterface
from core.entity_base_service import EntityBaseService
from application.services import (
    BookService, UserService, CartService, ShoppingSessionService
)
from application.tasks.tasks1 import send_order_summary_email


OrderId: TypeAlias = str
books_data: TypeAlias = str


class OrderService(EntityBaseService):
    def __init__(
        self,
        order_repo: Annotated[
            CombinedOrderRepositoryInterface, Depends(OrderRepository)
        ],
        book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
        book_order_assoc_repo: Annotated[
            CombinedBookOrderAssocRepoInterface, Depends(BookOrderAssocRepository)
        ],
        shopping_session_repo: Annotated[
            CombinedShoppingSessionRepositoryInterface, Depends(ShoppingSessionRepository)
        ],
        cart_repo: Annotated[
            CombinedCartRepositoryInterface, Depends(CartRepository)
        ],
        payment_detail_repo: Annotated[
            CombinedPaymentDetailRepoInterface, Depends(PaymentDetailRepository)
        ],
        book_service: Annotated[BookService, Depends(BookService)],
        user_service: Annotated[UserService, Depends(UserService)],
        cart_service: Annotated[CartService, Depends(CartService)],
        shopping_session_service: Annotated[
            ShoppingSessionService, Depends(ShoppingSessionService)
        ],
    ):
        super().__init__(
            payment_detail_repo=payment_detail_repo,
            shopping_session_repo=shopping_session_repo,
            order_repo=order_repo,
            book_order_assoc_repo=book_order_assoc_repo
        )
        self._order_repo = order_repo
        self._book_repo = book_repo
        self._user_service = user_service
        self._book_service = book_service
        self._shopping_session_service = shopping_session_service
        self._cart_service = cart_service
        self._cart_repo = cart_repo
        self._book_order_assoc_repo = book_order_assoc_repo
        self._shopping_session_repo = shopping_session_repo
        self._payment_detail_repo = payment_detail_repo

    async def create_order(
        self, session: AsyncSession, dto: CreateOrderS
    ) -> OrderIdS:
        dto: dict = dto.model_dump(exclude_unset=True)

        try:
            domain_model = OrderS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        _ = await self._user_service.get_user_by_id(
            session=session, id=domain_model.user_id
        )  # if no exception was raised

        order_id: int = await super().create(
            repo=self._order_repo,
            session=session,
            domain_model=domain_model
        )

        await super().commit(session=session)

        return OrderIdS(
            id=order_id
        )

    async def get_all_orders(
        self, session: AsyncSession, pagination: PaginationS
    ) -> list[ShortenedReturnOrderS]:
        orders: list[Order] = await self._order_repo.get_all_orders(
            session=session,
            page=pagination.page,
            limit=pagination.limit,
        )

        res: list[ShortenedReturnOrderS] = []

        for order in orders:
            order_owner_full_name = " ".join(
                [order.user.first_name, order.user.last_name]
            )
            res.append(
                ShortenedReturnOrderS(
                    owner_name=order_owner_full_name,
                    owner_email=order.user.email,
                    order_id=order.id,
                    order_status=order.order_status,
                    total_sum=order.total_sum,
                    order_date=order.order_date
                )
            )
        return res

    async def get_order_by_id(
        self, session: AsyncSession, order_id: int
    ) -> ReturnOrderS:

        order_details: list[BookOrderAssoc] = await super().get_by_id(
            session=session,
            repo=self._order_repo,
            id=order_id
        )

        books: list[AssocBookS] = order_assembler(order_details)

        return ReturnOrderS(
            order_id=order_id,
            books=books
        )

    async def get_orders_by_user_id(
            self,
            session: AsyncSession,
            user_id: int
    ) -> list[ReturnOrderS]:
        order_details: Union[BookOrderAssoc, None] = None

        try:
            order_details: list[BookOrderAssoc] = await self._order_repo.get_orders_by_user_id(
                session=session, user_id=user_id
            )  # details of orders made by a user
            logger.debug(
                "order_details in get_order_by_id",
                extra={"order_details": order_details}
            )
        except (NotFoundError, DBError) as e:
            if type(e) == NotFoundError:
                logger.info(f"{e.entity} not found", exc_info=True)
                raise EntityDoesNotExist(e.entity)
            elif type(e) == DBError:
                logger.error("DB error", exc_info=True)
                raise ServerError()

        orders: dict[OrderId, list[BookOrderAssoc]] = defaultdict(list)

        for order_detail in order_details:
            # arrange order details by order_ids
            orders[order_detail.order_id].append(order_detail)

        result_orders: list[ReturnOrderS] = []

        for order_id, details in orders.items():
            # for each order convert it into ReturnOrderS
            books: list[AssocBookS] = order_assembler(
                order_details=details
            )
            result_orders.append(
                ReturnOrderS(
                    order_id=int(order_id),
                    books=books
                )
            )

        return result_orders

    async def delete_order(
            self,
            session: AsyncSession,
            order_id: str | int
    ) -> None:
        await super().delete(
            repo=self._order_repo, session=session, instance_id=order_id
        )
        await super().commit(session=session)

    async def update_order(
        self,
        session: AsyncSession,
        order_id: int,
        dto: UpdatePartiallyOrderS,
    ):
        dto: dict = dto.model_dump(exclude_none=True, exclude_unset=True)
        try:
            domain_model = OrderS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError()

        return await super().update(
            repo=self._order_repo,
            session=session,
            instance_id=order_id,
            domain_model=domain_model,
        )

    async def add_book_to_order(
        self,
        order_id: int,
        session: AsyncSession,
        dto: AddBookToOrderS
    ) -> ReturnOrderS:
        order_books: list[BookOrderAssoc] = await super().get_by_id(
            session=session,
            repo=self._order_repo,
            id=order_id,
        )  # if no order http_exception will be raised

        book: Book = await self._book_repo.get_by_id(
            session=session,
            id=dto.book_id
        )  # if no book http_exception will be raised

        for order_detail in order_books:
            if str(order_detail.book_id) == str(dto.book_id):
                order: Order = order_detail.order
                order.total_sum += book.price_with_discount
                order_detail.count_ordered += dto.count_ordered
                await super().commit(session=session)
                return await self.get_order_by_id(session=session, order_id=order_id)

        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)

        try:
            domain_model = BookOrderAssocS(
                **dto,
                order_id=order_id
            )
            logger.info(
                "BookOrderAssocS",
                extra={"BookOrderAssocS": domain_model}
            )
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        _ = await super().create(
            session=session,
            repo=self._book_order_assoc_repo,
            domain_model=domain_model
        )

        order: Order = order_books[0].order
        order.total_sum += book.price_with_discount
        await super().commit(session=session)

        return await self.get_order_by_id(session=session, order_id=order_id)

    async def delete_book_from_order(
        self,
        session: AsyncSession,
        book_id: UUID,
        order_id: int,
    ) -> ReturnOrderS:
        try:
            _: list[BookOrderAssoc] = await super().get_by_id(
                session=session,
                repo=self._order_repo,
                id=order_id
            )
        except EntityDoesNotExist:
            raise EntityDoesNotExist("Book (in the order)")

        try:
            await self._order_repo.delete_book_from_order_by_id(
                session=session,
                book_id=book_id,
                order_id=order_id
            )
            return await self.get_order_by_id(session=session, order_id=order_id)
        except DBError:
            extra = {
                "book_id": book_id,
                "order_id": order_id
            }
            logger.error(
                "Failed to delete_book from order",
                exc_info=True,
                extra=extra
            )
            raise ServerError()

    async def make_order(
        self,
        session: AsyncSession,
        order_id: int,
    ):
        user: ReturnUserS = await self._user_service.get_user_by_order_id(
            session=session, order_id=order_id
        )

        user_with_orders: ReturnUserWithOrdersS = (
            await self._user_service.get_user_with_orders(
                session=session, user_id=user.id
            )
        )

        order_books: list[BookSummaryS] = []

        for order in user_with_orders.orders:
            if order.order_id == order_id:
                for book in order.books:
                    total_price = book.count_ordered * book.price_per_unit
                    book_summary = BookSummaryS(
                        name=book.name,
                        count_ordered=book.count_ordered,
                        total_price=total_price,
                    )
                    order_books.append(book_summary)
                break

        data = OrderSummaryS(
            username=user.name, email=user.email, books=order_books
        ).model_dump()

        send_order_summary_email.delay(
            order_data=data,
        )

    async def perform_order(
            self,
            payment_id: UUID,
            shopping_session_id: UUID,
            status: Literal["success", "failed"],
    ):
        """If status OK --> get cart ids of books, then add this
         books to order, change status of payment, delete cart"""
        async with db_client.async_session() as session:
            if status == "success":
                cart: ReturnCartS = await self._cart_service.get_cart_by_session_id(
                    session=session,
                    shopping_session_id=shopping_session_id
                )

                await self._payment_detail_repo.update(
                    session=session,
                    domain_model=PaymentDetailS(
                        status="success",
                    ),
                    instance_id=payment_id
                )  # update payment status

                print("UPDATED PAYMENT STATUS")

                shopping_session: ReturnShoppingSessionS = await self._shopping_session_service.get_shopping_session_by_id(
                    session=session,
                    id=shopping_session_id
                )

                cart_books: list[AssocBookS] = cart.books

                domain_models: list[BookOrderAssocS] = []

                order_dto = CreateOrderS(
                    user_id=shopping_session.user_id,
                    order_status="success"
                )

                order: OrderIdS = await self.create_order(
                    session=session,
                    dto=order_dto
                )  # create order

                for book in cart_books:
                    domain_models.append(
                        BookOrderAssocS(
                            book_id=book.book_id,
                            order_id=order.id,
                            count_ordered=book.count_ordered
                        )
                    )

                print("CREATED ORDER")

                try:
                    await self._book_order_assoc_repo.create_many(
                        session=session,
                        domain_models=domain_models
                    )  # take books from cart to order
                    print("ORDER IS FULFILLED WITH DATA")
                except DBError:
                    await session.rollback()
                    extra = {
                        "domain_models": domain_models
                    }
                    logger.error("failed to add data to order", exc_info=True, extra=extra)
                    raise ServerError("Failed to create order")

            try:
                await self._shopping_session_service.delete(
                    session=session,
                    repo=self._shopping_session_repo,
                    instance_id=shopping_session_id
                )  # delete cart with its items
            except DBError:
                await session.rollback()
                logger.error("failed to delete cart")
            print("CART DELETED")





