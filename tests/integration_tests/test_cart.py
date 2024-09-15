from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories import BookRepository, ImageRepository, CartRepository, ShoppingSessionRepository, \
    UserRepository, OrderRepository
from application.repositories.cart_repo import CombinedCartRepositoryInterface
from application.schemas import AddBookToCartS, ReturnCartS, ReturnBookS, DeleteBookFromCartS
from application.schemas.order_schemas import AssocBookS
from application.services import CartService, BookService, ShoppingSessionService, UserService
from application.services.storage.internal_storage.image_manager import ImageManager
from core.base_repos.unit_of_work import SqlAlchemyUnitOfWork
from core.exceptions import BadRequest, EntityDoesNotExist
from infrastructure.postgres.app import db_client
from application.services.storage.internal_storage.internal_storage_service import InternalStorageService


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def cart_service(
) -> CartService:

    uow = SqlAlchemyUnitOfWork()

    book_repo = BookRepository()
    image_repo = ImageRepository()
    cart_repo = CartRepository()
    user_repo = UserRepository()
    order_repo = OrderRepository()
    shopping_session_repo = ShoppingSessionRepository()
    image_manager = ImageManager()

    storage_service = InternalStorageService(
        book_repo=book_repo,
        image_manager=image_manager
    )
    book_service = BookService(
        storage=storage_service,
        book_repo=book_repo,
        image_repo=image_repo
    )
    shopping_session_service = ShoppingSessionService(
        shopping_session_repo=shopping_session_repo)
    user_service = UserService(
        user_repo=user_repo,
        order_repo=order_repo
    )

    service = CartService(
        cart_repo=cart_repo,
        book_repo=book_repo,
        uow=uow,
        book_service=book_service,
        shopping_session_service=shopping_session_service,
        user_service=user_service
    )
    return service

@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def shopping_session_service() -> ShoppingSessionService:
    shopping_session_repo = ShoppingSessionRepository()
    service = ShoppingSessionService(
        shopping_session_repo=shopping_session_repo
    )
    return service

@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def session():
    async with db_client.async_session() as session:
        yield session


@pytest.mark.asyncio(scope="session")
async def test_add_book_to_cart_for_the_first_time(
        cart_service: CartService,
        session: AsyncSession,
        shopping_session_service: ShoppingSessionService
):
    res: ReturnCartS = await cart_service.add_book_to_cart(
        session=session,
        shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc"),
        dto=AddBookToCartS(
            book_id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848"),
            quantity=1
            )
        )

    assert res == ReturnCartS(
        cart_id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
        books=[
            AssocBookS(
                book_id=UUID('20aaefdc-ab3b-4074-af87-dc26a36bb6a0'),
                book_title='Example book',
                authors=['Michael Jordan'],
                categories=['Category 1', 'Category 2'],
                rating=5,
                discount=0,
                count_ordered=1,
                price_per_unit=100
                ),
            AssocBookS(
                book_id=UUID('d2bafd10-4192-4930-aa40-9bcf4b39a848'),
                book_title='Example book 2 ',
                authors=['Alex Checkhov'],
                categories=[],
                rating=3,
                discount=0,
                count_ordered=1,
                price_per_unit=500.0,
                )
            ])

    session.expire_all()
    book: ReturnBookS = await cart_service._book_service.get_book_by_id(
        session=session,

        id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848")
    )
    shopping_session = await shopping_session_service.get_shopping_session_by_id(
        session=session,
        id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
    )

    assert shopping_session.total == 600

    assert book.number_in_stock == 199


@pytest.mark.asyncio(scope="session")
async def test_add_book_to_cart_for_the_second_time(
        cart_service: CartService,
        session: AsyncSession,
        shopping_session_service: ShoppingSessionService
):
    res: ReturnCartS = await cart_service.add_book_to_cart(
        session=session,
        shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc"),
        dto=AddBookToCartS(
            book_id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848"),
            quantity=1
            )
        )

    assert res == ReturnCartS(
        cart_id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
        books=[
            AssocBookS(
                book_id=UUID('20aaefdc-ab3b-4074-af87-dc26a36bb6a0'),
                book_title='Example book',
                authors=['Michael Jordan'],
                categories=['Category 1', 'Category 2'],
                rating=5,
                discount=0,
                count_ordered=1,
                price_per_unit=100
            ),
            AssocBookS(
                book_id=UUID('d2bafd10-4192-4930-aa40-9bcf4b39a848'),
                book_title='Example book 2 ',
                authors=['Alex Checkhov'],
                categories=[],
                rating=3,
                discount=0,
                count_ordered=2,
                price_per_unit=500.0,
            )
        ])

    book: ReturnBookS = await cart_service._book_service.get_book_by_id(
        session=session,
        id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848")
    )

    shopping_session = await shopping_session_service.get_shopping_session_by_id(
        session=session,
        id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
    )

    assert shopping_session.total == 1100

    assert book.number_in_stock == 198


@pytest.mark.asyncio(scope="session")
async def test_add_more_books_than_in_stock(
        cart_service: CartService,
        session: AsyncSession,
):
    with pytest.raises(BadRequest) as excinfo:
        _ = await cart_service.add_book_to_cart(
            session=session,
            shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc"),
            dto=AddBookToCartS(
                book_id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848"),
                quantity=100000
            )
        )

        assert "400: You're trying to order too many books, only 198 left in stock" in str(excinfo.value)


@pytest.mark.asyncio(scope="session")
async def test_delete_book_from_cart(
        cart_service: CartService,
        session: AsyncSession,
        shopping_session_service: ShoppingSessionService
):
    res: ReturnCartS = await cart_service.delete_book_from_cart(
        session=session,
        deletion_data=DeleteBookFromCartS(
            book_id=UUID('d2bafd10-4192-4930-aa40-9bcf4b39a848'),
            quantity=1
        ),
        shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc")
    )

    assert res == ReturnCartS(
        cart_id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
        books=[
            AssocBookS(
                book_id=UUID('20aaefdc-ab3b-4074-af87-dc26a36bb6a0'),
                book_title='Example book',
                authors=['Michael Jordan'],
                categories=['Category 1', 'Category 2'],
                rating=5,
                discount=0,
                count_ordered=1,
                price_per_unit=100
            ),
            AssocBookS(
                book_id=UUID('d2bafd10-4192-4930-aa40-9bcf4b39a848'),
                book_title='Example book 2 ',
                authors=['Alex Checkhov'],
                categories=[],
                rating=3,
                discount=0,
                count_ordered=1,
                price_per_unit=500.0,
            )
        ])

    session.expire_all()
    book: ReturnBookS = await cart_service._book_service.get_book_by_id(
        session=session,
        id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848")
    )

    shopping_session = await shopping_session_service.get_shopping_session_by_id(
        session=session,
        id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
    )

    assert shopping_session.total == 600
    assert book.number_in_stock == 199


@pytest.mark.asyncio(scope="session")
async def test_delete_all_books_from_cart(
        cart_service: CartService,
        session: AsyncSession,
        shopping_session_service: ShoppingSessionService
):
    res: ReturnCartS = await cart_service.delete_book_from_cart(
        session=session,
        deletion_data=DeleteBookFromCartS(
            book_id=UUID('d2bafd10-4192-4930-aa40-9bcf4b39a848'),
            quantity=1
        ),
        shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc")
    )

    assert res == ReturnCartS(
        cart_id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
        books=[
            AssocBookS(
                book_id=UUID('20aaefdc-ab3b-4074-af87-dc26a36bb6a0'),
                book_title='Example book',
                authors=['Michael Jordan'],
                categories=['Category 1', 'Category 2'],
                rating=5,
                discount=0,
                count_ordered=1,
                price_per_unit=100
            ),
        ])

    session.expire_all()
    book: ReturnBookS = await cart_service._book_service.get_book_by_id(
        session=session,
        id=UUID("d2bafd10-4192-4930-aa40-9bcf4b39a848")
    )

    shopping_session = await shopping_session_service.get_shopping_session_by_id(
        session=session,
        id=UUID('01e1ca73-5dea-46f2-a19b-56b5a7804efc'),
    )
    assert shopping_session.total == 100
    assert book.number_in_stock == 200


@pytest.mark.asyncio(scope="session")
async def test_delete_more_books_than_in_cart(
        cart_service: CartService,
        session: AsyncSession
):
    with pytest.raises(BadRequest) as excinfo:
        _ = await cart_service.delete_book_from_cart(
            session=session,
            deletion_data=DeleteBookFromCartS(
                book_id=UUID('20aaefdc-ab3b-4074-af87-dc26a36bb6a0'),
                quantity=1000
            ),
            shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc")
        )

        assert "You're trying to delete more books that there exists in the cart" in str(excinfo.value)


@pytest.mark.asyncio(scope="session")
async def test_delete_book_that_not_in_cart(
        cart_service: CartService,
        session: AsyncSession,
):
    with pytest.raises(EntityDoesNotExist) as excinfo:
        _ = await cart_service.delete_book_from_cart(
            session=session,
            deletion_data=DeleteBookFromCartS(
                book_id=UUID('17cfb58c-1dab-46d1-9f8d-9de15e111a4a'),
                quantity=1000
            ),
            shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc")
        )

        assert "Book (in a cart) does not exist" in str(excinfo.value)


@pytest.mark.asyncio(scope="session")
async def test_delete_expired_carts(
        cart_service: CartService,
        session: AsyncSession,
):
    cart_repo: CombinedCartRepositoryInterface = cart_service._cart_repo

    await cart_repo.delete_expired_carts()

    with pytest.raises(EntityDoesNotExist) as excinfo:
        await cart_service.get_cart_by_session_id(
            session=session,
            shopping_session_id=UUID("fcc5b6ea-dd92-4b89-9ad6-1d9700b970bc")
        )
    assert "Cart does not exist" in str(excinfo.value)