from aioredis import Redis, RedisError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from application import Book
from application.models import CartItem
from application.repositories.cart_repo import CombinedCartRepositoryInterface, CartRepository
from application.repositories.book_repo import BookRepository, CombinedBookRepoInterface
from application.schemas import AddBookToCartS, ReturnCartS, ShoppingSessionIdS, CreateShoppingSessionS, \
    DeleteBookFromCartS
from core.base_repos.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from application.services import UserService, ShoppingSessionService, BookService
from application.services.cart_service import store_cart_to_cache, serialize_and_store_cart_books
from application.services.cart_service.utils import \
    (
    cart_assembler
)

from auth.helpers import get_token_payload
from core import EntityBaseService
from typing import Annotated, Union
from application.schemas.domain_model_schemas import CartItemS, BookS

from uuid import UUID as uuid_UUID

from core.config import settings
from core.exceptions import NotFoundError, EntityDoesNotExist, DBError, ServerError, AlreadyExistsError, \
    AddBooksToCartError, BadRequest, DeleteBooksFromCartError
from infrastructure.redis import redis_client
from logger import logger


class CartService(EntityBaseService):

    def __init__(
            self,
            cart_repo: Annotated[
                CombinedCartRepositoryInterface, Depends(CartRepository)
            ],
            book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
            uow: Annotated[AbstractUnitOfWork, Depends(SqlAlchemyUnitOfWork)],
            shopping_session_service: ShoppingSessionService = Depends(),
            user_service: UserService = Depends(),
            book_service: BookService = Depends()
    ):
        self.cart_repo = cart_repo
        self.book_repo = book_repo
        super().__init__(
            cart_repo=cart_repo,
            book_repo=book_repo
        )
        self.shopping_session_service = shopping_session_service
        self.user_service = user_service
        self.book_service = book_service
        self.redis_con: Redis = redis_client.connection
        self.uow: AbstractUnitOfWork = uow

    @store_cart_to_cache(cache_time_seconds=350)
    async def get_cart_by_session_id(
            self,
            session: AsyncSession,
            shopping_session_id: uuid_UUID | None,
    ) -> ReturnCartS:
        """retrieves books in a cart and cart session_id"""
        cart: list[CartItem] = []
        try:
            cart: list[CartItem] = await self.cart_repo.get_cart_by_session_id(
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
        _ = await self.user_service.get_user_by_id(session=session, id=user_id)

        try:
            cart: list[CartItem] = await self.cart_repo.get_cart_by_user_id(
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

        shopping_session_id: ShoppingSessionIdS = await self.shopping_session_service.create_shopping_session(
            session=session,
            dto=CreateShoppingSessionS(
                user_id=user_id,
                total=0.0
            )
        )

        shopping_session = await self.shopping_session_service.get_shopping_session_by_id(
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
            repo=self.cart_repo,
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
        """Adds a book to the cart / increments amount of ordered books"""
        domain_model = CartItemS(
            **dto.model_dump(exclude_none=True),
            session_id=shopping_session_id
        )

        book = await self.book_service.get_book_by_id(
            session=session,
            id=dto.book_id
        )  # if not exists, exception will be raised

        if book.number_in_stock - domain_model.quantity < 0:
            raise BadRequest(
                detail=f"You're trying to order too many books, only {book.number_in_stock} left in stock"
            )

        cart: list[CartItem] = await self.cart_repo.get_cart_by_session_id(
            session=session,
            cart_session_id=shopping_session_id
        )

        for cart_item in cart:
            """check if book already in the cart, if it is, then 
            decrease the number of books it stock and increase the number of books in the cart"""

            book_domain_model: BookS = BookS.model_validate(
                cart_item.book,
                from_attributes=True
            )
            book_domain_model.price_with_discount = None
            #  computed field, we have to set it to None to avoid an error here

            if str(cart_item.book_id) == str(domain_model.book_id):
                cart_item_domain_model: CartItemS = CartItemS.model_validate(
                    cart_item,
                    from_attributes=True
                )

                try:
                    cart_item_domain_model.put_books_in_cart(
                        quantity=domain_model.quantity,
                        book=book_domain_model
                    )
                except AddBooksToCartError as e:
                    logger.debug("Failed to add books from cart", exc_info=True)
                    raise BadRequest(
                        detail=e.info
                    )

                async with self.uow as uow:
                    await uow.update(
                        orm_model=CartItem,
                        obj=cart_item_domain_model
                    )
                    await uow.update(
                        orm_model=Book,
                        obj=book_domain_model
                    )
                    await uow.commit()

                cart: ReturnCartS = await self.get_cart_by_session_id(
                    session=session,
                    shopping_session_id=shopping_session_id
                )
                return cart

        _ = await super().create(
            session=session,
            repo=self.cart_repo,
            domain_model=domain_model
            )  # add book to the cart

        session.expire_all()  # clear session cache to get fresh data
        updated_cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session,
            shopping_session_id=shopping_session_id
        )

        if self.redis_con is not None:
            for cart_book in updated_cart.books:
                if str(cart_book.book_id) == str(domain_model.book_id):
                    await serialize_and_store_cart_books(
                        book=cart_book,
                        redis_con=self.redis_con
                    )  # store book to redis cache

            cart_uq_key = f"cart:{shopping_session_id}"  # identifies of a set in cache

            await self.redis_con.sadd(
                cart_uq_key,
                str(domain_model.book_id)
            )  # update set of books in cache
        logger.error("Failed to update cart in cache")

        return updated_cart

    async def delete_book_from_cart(
            self,
            session: AsyncSession,
            deletion_data: DeleteBookFromCartS,
            shopping_session_id: uuid_UUID

    ) -> ReturnCartS:

        _ = await self.book_service.get_book_by_id(
            session=session,
            id=deletion_data.book_id
        )  # if not exists, exception will be raised

        cart: list[CartItem] = await self.cart_repo.get_cart_by_session_id(
            session=session,
            cart_session_id=shopping_session_id
        )

        for cart_item in cart:
            book_domain_model: BookS = BookS.model_validate(
                cart_item.book,
                from_attributes=True
            )
            book_domain_model.price_with_discount = None
            #  computed field, we have to set it to None to avoid an error here

            if str(book_domain_model.id) == str(deletion_data.book_id):
                # if we've found the book that we want to delete
                cart_item_domain_model: CartItemS = CartItemS.model_validate(
                    cart_item,
                    from_attributes=True
                )
                try:
                    cart_item_domain_model.remove_books_from_cart(
                        quantity=deletion_data.quantity,
                        book=book_domain_model
                    )  # update number of books in cart domain model
                except DeleteBooksFromCartError as e:
                    logger.debug("Failed to delete books from cart", exc_info=True)
                    raise BadRequest(detail=e.info)

                if cart_item_domain_model.quantity == 0:
                    # if the whole quantity of books should be deleted
                    try:
                        async with self.uow as uow:
                            await uow.update(
                                obj=book_domain_model,
                                orm_model=Book
                            )

                            await uow.delete(
                                obj=cart_item_domain_model,
                                orm_model=CartItem
                            )
                            await uow.commit()
                    except DBError:
                        raise ServerError()
                    logger.info("Books has been deleted from cart")
                    break

                else:
                    # if part of books should be deleted
                    try:
                        async with self.uow as uow:
                            await uow.update(
                                obj=book_domain_model,
                                orm_model=Book
                            )

                            await uow.update(
                                obj=cart_item_domain_model,
                                orm_model=CartItem
                            )
                            await uow.commit()
                    except DBError:
                        raise ServerError()
                    logger.info("Book has been updated in cart")
                    break

        session.expire_all()  # clear session cache to get fresh data
        cart: ReturnCartS = await self.get_cart_by_session_id(
            session=session,
            shopping_session_id=shopping_session_id
        )

        uq_book_name = f"book:{deletion_data.book_id}"

        if self.redis_con:
            try:
                await self.redis_con.srem(
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

        return cart



