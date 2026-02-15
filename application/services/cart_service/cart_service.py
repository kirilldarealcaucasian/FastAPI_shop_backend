from uuid import UUID as uuid_UUID  # noqa

from aioredis import Redis, RedisError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import Book, CartItem
from ...repositories.book_repo import CombinedBookRepoInterface
from ...repositories.cart_repo import (
    CombinedCartRepositoryInterface,
)
from ...schemas import (
    AddBookToCartS,
    CreateShoppingSessionS,
    DeleteBookFromCartS,
    ReturnCartS,
)
from ...schemas.domain_model_schemas import BookS
from ...services import BookService, ShoppingSessionService, UserService
from .cart_assembler import assemble_cart
from ...services.entity_base_service import EntityBaseService
from ...settings import settings
from ...exceptions import (
    AlreadyExistsError,
    BadRequest,
    DBError,
    EntityDoesNotExist,
    NotFoundError,
    ServerError,
    ConflictErrorHTTP,
    ConflictError,
)
from ...types import CartPrimaryIdentifier
from dataclasses import dataclass


@dataclass(slots=True)
class CartService(EntityBaseService):
    book_repo: CombinedBookRepoInterface
    cart_repo: CombinedCartRepositoryInterface
    shopping_session_service: ShoppingSessionService
    user_service: UserService
    book_service: BookService
    redis_con: Redis | None = None

    async def get_cart_by_session_id(
        self,
        session: AsyncSession,
        shopping_session_id: uuid_UUID,
    ) -> ReturnCartS:
        try:
            cart: list[CartItem] = await self.cart_repo.get_cart_by_session_id(
                session=session,
                cart_session_id=shopping_session_id,
            )
        except (NotFoundError, DBError) as e:
            if isinstance(e, NotFoundError):
                raise EntityDoesNotExist(e.entity) from e
            raise ServerError() from e

        assembled_cart: ReturnCartS | None = assemble_cart(cart)  # converts data into
        if assembled_cart is None:
            logger.bind(shopping_session_id=shopping_session_id).error(
                "failed to get cart by session id: failed to assemble cart"
            )
            raise ServerError()

        return assembled_cart

    async def get_cart_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> ReturnCartS:
        cart: list[CartItem] = []
        _ = await self.user_service.get_user_by_id(session=session, id=user_id)

        try:
            cart: list[CartItem] = await self.cart_repo.get_cart_by_user_id(
                session=session, user_id=user_id
            )
        except (NotFoundError, DBError) as e:
            if isinstance(e, NotFoundError):
                raise EntityDoesNotExist("Cart") from e
            raise ServerError() from e
        assembled_cart: ReturnCartS | None = assemble_cart(cart)
        if assembled_cart is None:
            logger.bind(user_id=user_id).error(
                "failed to get cart by user id: failed to assemble cart"
            )
            raise ServerError()
        return assembled_cart

    async def create_cart(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> JSONResponse:
        """Cart is associated with a shopping_session_id.
        This method creates a shopping_session and stores it to the cookie"""
        try:
            if await self.get_cart_by_user_id(session=session, user_id=user_id):
                raise AlreadyExistsError(
                    entity="Cart",
                )
        except EntityDoesNotExist:
            # it is okay if there is no cart for a user
            pass

        shopping_session_id = (
            await self.shopping_session_service.create_shopping_session(
                session=session, dto=CreateShoppingSessionS(user_id=user_id, total=0.0)
            )
        )

        shopping_session = (
            await self.shopping_session_service.get_shopping_session_by_id(
                session=session, id=shopping_session_id
            )
        )

        response = JSONResponse(content={"status": "success"}, status_code=201)

        response.set_cookie(
            key=settings.SHOPPING_SESSION_COOKIE_NAME,
            value=str(shopping_session.id),
            expires=shopping_session.expiration_time,
            httponly=True,
            secure=True,
        )

        return response

    async def delete_cart(
        self,
        session: AsyncSession,
        cart_session_id: uuid_UUID,
    ) -> None:
        _ = await super().delete(
            repo=self.cart_repo, session=session, instance_id=cart_session_id
        )
        await super().commit(session=session)

    async def add_book_to_cart(
        self,
        session: AsyncSession,
        shopping_session_id: uuid_UUID,
        dto: AddBookToCartS,
    ) -> ReturnCartS:
        """Adds a book to the cart / increments the amount of books in a cart"""
        book: Book = await self.book_repo.get_by_id(session=session, id=dto.book_id)

        if not book:
            raise EntityDoesNotExist(entity="Book")

        book_domain_model: BookS = BookS.model_validate(book, from_attributes=True)
        if not book_domain_model.is_enough_in_stock(dto.quantity):
            raise BadRequest(
                detail=f"You're trying to order too many books, only \
                    {book.number_in_stock} left in stock"
            )

        await self.cart_repo.create_or_update_book_in_cart(
            session=session,
            session_id=shopping_session_id,
            book_id=book.id,
            quantity=dto.quantity,
        )

        updated_cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session, shopping_session_id=shopping_session_id
        )

        return updated_cart

    async def delete_book_from_cart(
        self,
        session: AsyncSession,
        deletion_data: DeleteBookFromCartS,
        shopping_session_id: uuid_UUID,
    ) -> ReturnCartS:
        """Deletes a book from the cart / decrements the amount of books in a cart"""
        book: Book | None = await self.book_repo.get_by_id(
            session=session, id=deletion_data.book_id
        )

        if not book:
            raise EntityDoesNotExist(entity="Book (in a cart)")

        cart_item: CartItem | None = await self.cart_repo.get_by_id(
            session=session,
            id=CartPrimaryIdentifier(
                book_id=deletion_data.book_id, session_id=shopping_session_id
            ),
        )

        if cart_item is None:
            raise EntityDoesNotExist(entity="Book (in cart)")

        if cart_item.quantity == deletion_data.quantity:
            try:
                await self.cart_repo.delete_all_books_from_cart(
                    session=session,
                    session_id=shopping_session_id,
                    book_id=deletion_data.book_id,
                )
            except ConflictError as e:
                logger.bind(
                    shopping_session_id=shopping_session_id,
                    book_id=deletion_data.book_id,
                    quantity=deletion_data.quantity,
                ).error("failed to delete all books from cart:", exc_info=True)
                raise ConflictErrorHTTP() from e
        else:
            try:
                await self.cart_repo.delete_some_books_from_cart(
                    session=session,
                    session_id=shopping_session_id,
                    book_id=deletion_data.book_id,
                    quantity=deletion_data.quantity,
                )
            except ConflictError as e:
                logger.bind(
                    shopping_session_id=shopping_session_id,
                    book_id=deletion_data.book_id,
                    quantity=deletion_data.quantity,
                ).opt(exception=e).error("failed to delete some books from cart:")
                raise ConflictErrorHTTP() from e
        logger.bind(
            shopping_session_id=shopping_session_id,
            book_id=deletion_data.book_id,
            quantity=deletion_data.quantity,
        ).info("deleted book(s) from cart")

        updated_cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session, shopping_session_id=shopping_session_id
        )

        try:
            if self.redis_con:
                uq_book_name = f"book:{deletion_data.book_id}"
                try:
                    await self.redis_con.srem(
                        uq_book_name, str(deletion_data.book_id)
                    )  # delete book from cache
                except RedisError:
                    extra = {
                        "uq_book_name": uq_book_name,
                        "books_id": deletion_data.book_id,
                    }
                    logger.error(
                        "Redis error. Something went wrong while deleting \
                        book from the cache",
                        extra=extra,
                        exc_info=True,
                    )
        except RedisError as e:
            logger.opt(exception=e).warning("failed to cache book")
        return updated_cart
