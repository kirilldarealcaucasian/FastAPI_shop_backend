from collections import defaultdict
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import Book, PaymentDetail
from application.repositories.book_order_assoc_repo import BookOrderAssocRepository, CombinedBookOrderAssocRepoInterface
from application.repositories.book_repo import CombinedBookRepoInterface
from application.repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from application.repositories.payment_detail_repo import CombinedPaymentDetailRepoInterface, PaymentDetailRepository
from application.repositories.shopping_session_repo import CombinedShoppingSessionRepositoryInterface
from application.schemas.domain_model_schemas import OrderS, BookOrderAssocS, PaymentDetailS, BookS
from application.services.order_service.utils import order_assembler
from application.services.utils.filters import Pagination
from core.base_repos import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from core.exceptions import (
    EntityDoesNotExist,
    DomainModelConversionError, NotFoundError,
    DBError, ServerError, PaymentFailedError, BadRequest, AddBookToOrderError
)
from application.schemas import (
    ReturnOrderS,
    CreateOrderS,
    ShortenedReturnOrderS,
    UpdatePartiallyOrderS, ReturnCartS, ReturnShoppingSessionS, BookOrderPrimaryIdentifier,
)

from application.repositories.order_repo import (
    OrderRepository,
)
from application.repositories.shopping_session_repo import (
    ShoppingSessionRepository
)
from application.repositories.book_repo import BookRepository

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
            uow: Annotated[AbstractUnitOfWork, Depends(SqlAlchemyUnitOfWork)]
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
        self._uow: AbstractUnitOfWork = uow

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

        return OrderIdS(
            id=order_id
        )

    async def get_all_orders(
            self, session: AsyncSession, pagination: PaginationS
    ) -> list[ShortenedReturnOrderS]:
        orders: list[Order] = await self._order_repo.get_all_orders(
            session=session,
            pagination=Pagination(
                limit=pagination.limit,
                page=pagination.page,
            )
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

        exists: bool = await self._order_repo.check_if_order_exists(
            session=session,
            order_id=order_id
        )

        if not exists:
            raise EntityDoesNotExist(
                entity="Order",
            )

        try:
            order_details: list[BookOrderAssoc] = await super().get_by_id(
                session=session,
                repo=self._order_repo,
                id=order_id
            )
        except EntityDoesNotExist:
            return ReturnOrderS(
                order_id=order_id,
                books=[]
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

    async def get_order_details_by_payment_id(
            self,
            session: AsyncSession,
            payment_id: UUID
    ) -> ReturnOrderS:
        try:
            order: Order = await self._order_repo.get_order_by_payment_id(
                session=session,
                payment_id=payment_id
            )
        except (NotFoundError, DBError) as e:
            if type(e) == NotFoundError:
                raise EntityDoesNotExist(
                    entity=e.entity
                )
            else:
                logger.error("failed to get payment by id", exc_info=True)
                raise ServerError()

        order_details: list[BookOrderAssoc] = order.order_details

        books: list[AssocBookS] = order_assembler(order_details)

        return ReturnOrderS(
            order_id=order.id,
            books=books
        )

    async def get_order_summary(
            self,
            session: AsyncSession,
            payment_id: UUID
    ) -> OrderS:
        try:
            order: Order = await self._order_repo.get_order_summary(
                session=session,
                payment_id=payment_id
            )
            order_domain_model: OrderS = OrderS.model_validate(
                order, from_attributes=True
            )
            return order_domain_model
        except (NotFoundError, DBError) as e:
            if type(e) == NotFoundError:
                raise EntityDoesNotExist(
                    entity=e.entity
                )
            else:
                logger.error("failed to get payment by id", exc_info=True)
                raise ServerError()

    async def delete_order(
            self,
            session: AsyncSession,
            order_id: int
    ) -> None:
        exists: bool = await self._order_repo.check_if_order_exists(
            session=session,
            order_id=order_id
        )
        if not exists:
            raise EntityDoesNotExist(
                entity="Order"
            )

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
        book: Book = await self._book_repo.get_by_id(
            session=session,
            id=dto.book_id
        )  # if no book http_exception will be raised

        if not book:
            raise EntityDoesNotExist(
                entity="Book"
            )

        book_domain_model: BookS = BookS.model_validate(book, from_attributes=True)

        if book_domain_model.number_in_stock - dto.count_ordered < 0:
            raise BadRequest(
                detail=f"You're trying to order too many books, only {book.number_in_stock} left in stock"
            )

        order_item: Union[BookOrderAssoc, None] = await self._book_order_assoc_repo.get_by_id(
            session=session,
            id=BookOrderPrimaryIdentifier(
                order_id=order_id,
                book_id=dto.book_id
            )
        )

        order_item_exists: bool = True if order_item is not None else False

        if not order_item_exists:
            # if there is no book in the order yet
            extra = {
                "order_id": order_id,
                "book_id": dto.book_id
            }

            logger.debug("cart_item wasn't found", extra=extra)
            order_item_domain_model: BookOrderAssocS = BookOrderAssocS(
                **dto.model_dump(exclude_none=True),
                order_id=order_id
            )

            _ = await super().create(
                session=session,
                repo=self._book_order_assoc_repo,
                domain_model=order_item_domain_model
            )  # add book to the cart, if not added, http exception will be raised
            logger.debug("order_item was created", extra=extra)

        if not order_item_exists:
            session.expire_all()
            order_item: BookOrderAssoc = await self._book_order_assoc_repo.get_by_id(
                session=session,
                id=BookOrderPrimaryIdentifier(
                    book_id=dto.book_id,
                    order_id=order_id
                )
            )

        order_item_domain_model = BookOrderAssocS(
            book_id=dto.book_id,
            order_id=order_id,
            count_ordered=order_item.count_ordered
        )

        order: Order = order_item.order
        order_domain_model: OrderS = OrderS.model_validate(
            obj=order,
            from_attributes=True
        )

        try:
            order_item_domain_model.put_books_in_order(
                quantity=dto.count_ordered,
                book=book_domain_model,
                order=order_domain_model
            )
        except AddBookToOrderError as e:
            raise BadRequest(str(e.info))

        async with self._uow as uow:
            # increment the number of ordered books in the order
            # update number_in_stock for the book
            # update total in order
            if order_item_exists:
                print("order_item_domain_model: ", order_item_domain_model)
                await uow.update(
                    orm_model=BookOrderAssoc,
                    obj=order_item_domain_model
                )

            await uow.update(
                orm_model=Book,
                obj=book_domain_model
            )
            print("order_domain_model: ", order_domain_model)
            await uow.update(
                orm_model=Order,
                obj=order_domain_model
            )
            await uow.commit()

        session.expire_all()
        updated_order: ReturnOrderS = await self.get_order_by_id(
            session=session,
            order_id=order_id
        )

        return updated_order

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

    async def perform_order(
            self,
            payment_id: UUID,
            shopping_session_id: UUID,
            status: Literal["success", "failed"],
    ):
        """If status is "success" -> transactionally update payment status
        and create order with status created. Then copy books from cart
        to order details, updating order total sum and then change status
        of order to success. After, delete the cart"""
        async with db_client.async_session() as session:
            try:
                payment_details: PaymentDetail = await self._payment_detail_repo.get_by_id(
                    session=session,
                    id=payment_id
                )
            except (NotFoundError, DBError) as e:
                if type(e) == NotFoundError:
                    raise EntityDoesNotExist("Payment object")
                else:
                    raise ServerError("failed to create order")

            if status == "success":
                logger.debug("payment status is successful")
                cart: ReturnCartS = await self._cart_service.get_cart_by_session_id(
                    session=session,
                    shopping_session_id=shopping_session_id
                )

                shopping_session: ReturnShoppingSessionS = await self._shopping_session_service \
                    .get_shopping_session_by_id(
                    session=session,
                    id=shopping_session_id
                )
                try:
                    async with self._uow as uow:
                        payment_update_obj = PaymentDetailS(
                            id=payment_id,
                            status="success",
                        )
                        await uow.update(
                            obj=payment_update_obj,
                            orm_model=PaymentDetail
                        )  # update payment status

                        cart_books: list[AssocBookS] = cart.books

                        order_domain_models: list[BookOrderAssocS] = []

                        order_create_obj = OrderS(
                            user_id=shopping_session.user_id,
                            order_status="success",
                            payment_id=payment_id,
                            total_sum=payment_details.amount
                        )  # create order obj
                        uow.add(
                            obj=order_create_obj,
                            orm_model=Order
                        )  # create order
                        await uow.commit()
                except DBError:
                    extra = {
                        "payment_id": payment_id,
                        "shopping_session_id": shopping_session_id,
                        "payment_status": "success"
                    }
                    logger.error(
                        "Failed to change payment status to 'success' or create order or both",
                        extra=extra
                    )
                    raise PaymentFailedError(
                        detail="Failed to create order. Refund is coming soon."
                    )

                order: Order = await self._order_repo.get_order_by_payment_id(
                    session=session,
                    payment_id=payment_id
                )  # retrieve previously created order

                for book in cart_books:  # prepare books to be copied from cart to order
                    order_domain_models.append(
                        BookOrderAssocS(
                            book_id=book.book_id,
                            order_id=order.id,
                            count_ordered=book.count_ordered
                        )
                    )

                try:
                    await self._book_order_assoc_repo.create_many(
                        session=session,
                        domain_models=order_domain_models
                    )  # copy books from cart to order
                    await super().commit(session=session)
                    logger.info("order has been created and filled successfully")
                except (ServerError, DBError):
                    order_domain_model = OrderS(
                        order_status="failed"
                    )
                    await super().update(  # updates order status to "failed"
                        repo=self._order_repo,
                        session=session,
                        instance_id=payment_id,
                        domain_model=order_domain_model
                    )
                    extra = {
                        "payment_id": payment_id,
                        "shopping_session_id": shopping_session_id,
                        "order_domain_models": order_domain_models
                    }
                    logger.error("failed to copy books from cart to order", exc_info=True, extra=extra)
                    raise PaymentFailedError(detail="Failed to create order. Refund is coming soon.")

                try:
                    await self._shopping_session_service.delete(
                        session=session,
                        repo=self._shopping_session_repo,
                        instance_id=shopping_session_id
                    )  # delete cart with its items
                except DBError:
                    extra = {"shopping_session_id": shopping_session_id}
                    logger.error("failed to delete cart", extra=extra)

            else:
                logger.debug("payment status is 'failed'")
                payment_domain_model = PaymentDetailS(
                    id=payment_id,
                    status="failed"
                )
                _ = await super().update(
                    session=session,
                    repo=self._payment_detail_repo,
                    instance_id=payment_id,
                    domain_model=payment_domain_model
                )  # update payment status to failed
                raise PaymentFailedError(detail="Payment was failed.")

