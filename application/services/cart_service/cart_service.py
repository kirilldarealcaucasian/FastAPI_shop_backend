from aioredis import Redis, RedisError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import CartItem, Book, ShoppingSession
from application.repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from application.repositories.book_repo import BookRepository, CombinedBookRepoInterface
from application.schemas import AddBookToCartS, ReturnCartS, ShoppingSessionIdS, CreateShoppingSessionS, \
    DeleteBookFromCartS, CartPrimaryIdentifier
from core.base_repos.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from application.services import UserService, ShoppingSessionService, BookService
from application.services.cart_service import store_cart_to_cache, serialize_and_store_cart_books, cart_assembler

from auth.helpers import get_token_payload
from core import EntityBaseService
from typing import Annotated, Union
from application.schemas.domain_model_schemas import CartItemS, BookS, ShoppingSessionS

from uuid import UUID as uuid_UUID  # noqa

from core.config import settings
from core.exceptions import NotFoundError, EntityDoesNotExist, DBError, ServerError, AlreadyExistsError, \
    AddBooksToCartError, BadRequest, DeleteBooksFromCartError
from infrastructure.redis import redis_client
from logger import logger


class CartService(EntityBaseService):

    def __init__(
            self,
            book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
            cart_repo: Annotated[CombinedCartRepositoryInterface, Depends(CartRepository)],
            shopping_session_service: Annotated[
                ShoppingSessionService, Depends(ShoppingSessionService)
            ],
            user_service: Annotated[UserService, Depends(UserService)],
            book_service: Annotated[BookService, Depends(BookService)],
            uow: Annotated[AbstractUnitOfWork, Depends(SqlAlchemyUnitOfWork)],
    ):
        self._cart_repo = cart_repo
        self._book_repo = book_repo
        super().__init__(
            cart_repo=cart_repo,
            book_repo=book_repo
        )
        self._shopping_session_service: ShoppingSessionService = shopping_session_service
        self._user_service: UserService = user_service
        self._book_service: BookService = book_service
        self._redis_con: Redis = redis_client.connection
        self._uow: AbstractUnitOfWork = uow

    @store_cart_to_cache(cache_time_seconds=350)
    async def get_cart_by_session_id(
            self,
            session: AsyncSession,
            shopping_session_id: uuid_UUID | None,
    ) -> ReturnCartS:
        """retrieves books in a cart and cart session_id"""
        cart: list[CartItem] = []
        try:
            cart: list[CartItem] = await self._cart_repo.get_cart_by_session_id(
                session=session,
                cart_session_id=shopping_session_id,
            )
        except (NotFoundError, DBError) as e:
            if type(e) == NotFoundError:
                logger.info(f"{e.entity} not found", exc_info=True)
                raise EntityDoesNotExist(e.entity)
            elif type(e) == DBError:
                logger.error("DB error", exc_info=True)
                raise ServerError()

        assembled_cart: ReturnCartS = cart_assembler(cart)  # converts data into ReturnCartS

        return assembled_cart

    @store_cart_to_cache(cache_time_seconds=350)
    async def get_cart_by_user_id(
            self,
            session: AsyncSession,
            user_id: int | str
    ) -> ReturnCartS:
        cart: list[CartItem] = []
        _ = await self._user_service.get_user_by_id(session=session, id=user_id)

        try:
            cart: list[CartItem] = await self._cart_repo.get_cart_by_user_id(
                session=session,
                user_id=user_id
            )
        except (NotFoundError, DBError) as e:
            if type(e) == NotFoundError:
                raise EntityDoesNotExist("Cart")
            elif type(e) == DBError:
                raise ServerError()

        assembled_cart: ReturnCartS = cart_assembler(cart)
        return assembled_cart

    async def create_cart(
            self,
            session: AsyncSession,
            credentials: HTTPAuthorizationCredentials | None
    ) -> JSONResponse:
        """Cart is associated with a shopping_session_id.
        This method creates a shopping_session and stores it to the cookie"""

        user_id: Union[int, None] = None

        if credentials:
            token_payload: dict = get_token_payload(
                credentials=credentials
            )
            user_id = token_payload["user_id"]
            try:
                cart = await self.get_cart_by_user_id(
                    session=session,
                    user_id=user_id
                )
                if cart:
                    raise AlreadyExistsError(
                        entity="Cart",
                    )
            except EntityDoesNotExist:
                # it is okay if there is no cart for a user
                pass

        shopping_session_id: ShoppingSessionIdS = await self._shopping_session_service.create_shopping_session(
            session=session,
            dto=CreateShoppingSessionS(
                user_id=user_id,
                total=0.0
            )
        )

        shopping_session = await self._shopping_session_service.get_shopping_session_by_id(
            session=session,
            id=shopping_session_id.session_id
        )

        response = JSONResponse(
            content={"status": "success"},
            status_code=201
        )

        response.set_cookie(
            key=settings.SHOPPING_SESSION_COOKIE_NAME,
            value=str(shopping_session.id),
            expires=shopping_session.expiration_time,
            httponly=True,
            secure=True
        )

        return response

    async def delete_cart(
            self,
            session: AsyncSession,
            cart_session_id: uuid_UUID,
    ) -> None:
        _ = await super().delete(
            repo=self._cart_repo,
            session=session,
            instance_id=cart_session_id
        )
        await super().commit(session=session)

    async def add_book_to_cart(
            self,
            session: AsyncSession,
            shopping_session_id: uuid_UUID,
            dto: AddBookToCartS,
    ) -> ReturnCartS:
        """Adds a book to the cart / increments the amount of books in a cart"""
        book: Book = await self._book_repo.get_by_id(
            session=session,
            id=dto.book_id
        )

        if not book:
            raise EntityDoesNotExist(
                entity="Book"
            )

        book_domain_model: BookS = BookS.model_validate(book, from_attributes=True)

        if book_domain_model.number_in_stock - dto.quantity < 0:
            raise BadRequest(
                detail=f"You're trying to order too many books, only {book.number_in_stock} left in stock"
            )

        cart_item: Union[CartItem, None] = await self._cart_repo.get_by_id(
            session=session,
            id=CartPrimaryIdentifier(
                book_id=dto.book_id,
                session_id=shopping_session_id
            )
        )  # check if book already exists in the cart
        cart_item_exists: bool = True if cart_item is not None else False

        if not cart_item_exists:
            # if there is no book in the cart yet
            extra = {
                "shopping_session_id": shopping_session_id,
                "book_id": dto.book_id
            }
            logger.debug("cart_item wasn't found", extra=extra)

            cart_item_domain_model: CartItemS = CartItemS(
                    **dto.model_dump(exclude_none=True),
                    session_id=shopping_session_id
                    )

            _ = await super().create(
                session=session,
                repo=self._cart_repo,
                domain_model=cart_item_domain_model
                )  # add book to the cart, if not added, http exception will be raised
            logger.debug("cart_item was created", extra=extra)

        if not cart_item_exists:
            cart_item: CartItem = await super().get_by_id(
                session=session,
                repo=self._cart_repo,
                id=CartPrimaryIdentifier(
                    book_id=dto.book_id,
                    session_id=shopping_session_id
                )
            )

        cart_item_domain_model: CartItemS = CartItemS.model_validate(
            obj=cart_item,
            from_attributes=True
        )

        shopping_session: ShoppingSession = cart_item.shopping_session
        shopping_session_domain_model: ShoppingSessionS = ShoppingSessionS.model_validate(
            obj=shopping_session,
            from_attributes=True
        )

        try:
            cart_item_domain_model.put_books_in_cart(
                quantity=dto.quantity,
                book=book_domain_model,
                shopping_session=shopping_session_domain_model
            )
        except AddBooksToCartError as e:
            raise BadRequest(str(e.info))

        async with self._uow as uow:
            # increment the number of ordered books in a cart
            # update number_in_stock for the book
            # update total in shopping_session
            if cart_item_exists:
                await uow.update(
                    orm_model=CartItem,
                    obj=cart_item_domain_model
                )
            await uow.update(
                orm_model=Book,
                obj=book_domain_model
            )
            await uow.update(
                orm_model=ShoppingSession,
                obj=shopping_session_domain_model
            )
            await uow.commit()

        session.expire_all()
        updated_cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session,
            shopping_session_id=shopping_session_id
        )

        if self._redis_con is not None:
            for cart_book in updated_cart.books:
                if str(cart_book.book_id) == str(dto.book_id):
                    await serialize_and_store_cart_books(
                        book=cart_book,
                        redis_con=self._redis_con
                    )  # store book to redis cache

            cart_uq_key = f"cart:{shopping_session_id}"  # identifier of a set in cache

            await self._redis_con.sadd(
                cart_uq_key,
                str(dto.book_id)
            )  # update set of books in cache
            logger.error("Failed to update cart in cache")

        return updated_cart

    async def delete_book_from_cart(
            self,
            session: AsyncSession,
            deletion_data: DeleteBookFromCartS,
            shopping_session_id: uuid_UUID
    ) -> ReturnCartS:
        """Deletes a book from the cart / decrements the amount of books in a cart"""
        book: Union[Book, None] = await self._book_repo.get_by_id(
            session=session,
            id=deletion_data.book_id
        )

        if not book:
            raise EntityDoesNotExist(entity="Book (in a cart)")

        book_domain_model: BookS = BookS.model_validate(book, from_attributes=True)

        cart_item: Union[CartItem, None] = await self._cart_repo.get_by_id(
            session=session,
            id=CartPrimaryIdentifier(
                book_id=deletion_data.book_id,
                session_id=shopping_session_id
            )
        )

        if not cart_item:
            raise EntityDoesNotExist(entity="Book (in cart)")

        cart_item_domain_model: CartItemS = CartItemS.model_validate(
            cart_item,
            from_attributes=True
        )

        shopping_session: ShoppingSession = cart_item.shopping_session
        shopping_session_domain_model: ShoppingSessionS = ShoppingSessionS.model_validate(
            shopping_session,
            from_attributes=True
        )

        try:
            cart_item_domain_model.remove_books_from_cart(
                quantity=deletion_data.quantity,
                book=book_domain_model,
                shopping_session=shopping_session_domain_model
                )
        except DeleteBooksFromCartError as e:
            logger.debug("Failed to delete books from cart", exc_info=True)
            raise BadRequest(detail=e.info)

        try:
            async with self._uow as uow:
                # update number_in_stock for book
                # delete book from the cart or update # noqa
                # update total in shopping_session
                await uow.update(
                    obj=book_domain_model,
                    orm_model=Book
                )

                if cart_item_domain_model.quantity == 0:
                    cart_item_instance_to_delete = CartItem(
                        session_id=cart_item_domain_model.session_id,
                        book_id=book_domain_model.id,
                    )
                    await uow.delete(
                        orm_obj=cart_item_instance_to_delete
                    )
                elif cart_item_domain_model.quantity >= 0:
                    await uow.update(
                        orm_model=CartItem,
                        obj=cart_item_domain_model
                    )

                await uow.update(
                    orm_model=ShoppingSession,
                    obj=shopping_session_domain_model
                )
                await uow.commit()
        except DBError:
            logger.info("Book has been deleted from a cart")
            raise ServerError()

        session.expire_all()
        updated_cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session,
            shopping_session_id=shopping_session_id
        )
        if self._redis_con:
            uq_book_name = f"book:{deletion_data.book_id}"
            try:
                await self._redis_con.srem(
                    uq_book_name,
                    str(deletion_data.book_id)
                )  # delete book from cache
            except RedisError:
                extra = {
                    "uq_book_name": uq_book_name,
                    "books_id": deletion_data.book_id
                }
                logger.error(
                    "Redis error. Something went wrong while deleting book from the cache",
                    extra=extra,
                    exc_info=True
                )
        return updated_cart
