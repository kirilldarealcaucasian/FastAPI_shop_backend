import uuid
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories import BookRepository, ImageRepository, CartRepository, ShoppingSessionRepository, \
    UserRepository, OrderRepository, PaymentDetailRepository
from application.repositories.book_order_assoc_repo import BookOrderAssocRepository
from application.schemas import ReturnOrderS
from application.schemas.domain_model_schemas import PaymentDetailS, OrderS
from application.services import BookService, ShoppingSessionService, UserService, OrderService, CartService, \
    PaymentService
from application.services.storage.internal_storage.image_manager import ImageManager
from core.base_repos.unit_of_work import SqlAlchemyUnitOfWork
from core.exceptions import PaymentFailedError
from infrastructure.payment.yookassa.app import YooKassaPaymentProvider
from infrastructure.postgres.app import db_client
from application.services.storage.internal_storage.internal_storage_service import InternalStorageService


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def order_service(
) -> OrderService:
    uow = SqlAlchemyUnitOfWork()

    book_repo = BookRepository()
    image_repo = ImageRepository()
    cart_repo = CartRepository()
    user_repo = UserRepository()
    order_repo = OrderRepository()
    shopping_session_repo = ShoppingSessionRepository()
    book_order_assoc_repo = BookOrderAssocRepository()
    payment_detail_repo = PaymentDetailRepository()

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

    cart_service = CartService(
        book_repo=book_repo,
        cart_repo=cart_repo,
        shopping_session_service=shopping_session_service,
        user_service=user_service,
        book_service=book_service,
        uow=uow
    )


    service = OrderService(
        order_repo=order_repo,
        book_repo=book_repo,
        book_order_assoc_repo=book_order_assoc_repo,
        shopping_session_repo=shopping_session_repo,
        cart_repo=cart_repo,
        payment_detail_repo=payment_detail_repo,
        book_service=book_service,
        user_service=user_service,
        cart_service=cart_service,
        shopping_session_service=shopping_session_service,
        uow=uow,
    )
    return service


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def payment_service(order_service: OrderService) -> PaymentService:
    payment_provider = YooKassaPaymentProvider()
    shopping_session_repo = ShoppingSessionRepository()
    cart_repo = CartRepository()
    payment_detail_repo = PaymentDetailRepository()

    service = PaymentService(
        payment_provider=payment_provider,
        shopping_session_repo=shopping_session_repo,
        cart_repo=cart_repo,
        payment_detail_repo=payment_detail_repo
    )

    return service


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def session():
    async with db_client.async_session() as session:
        yield session


async def test_perform_order(
        order_service: OrderService,
        payment_service: PaymentService,
        session: AsyncSession
):
    payment_id: UUID = uuid.uuid4()

    payment_detail_repo = PaymentDetailRepository()
    domain_model = PaymentDetailS(
        id=payment_id,
        status="pending",
        payment_provider="yookassa",
        amount=1000.0
    )

    await payment_detail_repo.create(
        session=session,
        domain_model=domain_model
    )  # create fake payment

    _ = await order_service.perform_order(
        payment_id=payment_id,
        shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc"),
        status="success",
    )

    payment: PaymentDetailS = await payment_service.get_by_id(
        repo=payment_service._payment_detail_repo,
        session=session,
        id=payment_id
    )

    payment_to_pydantic: PaymentDetailS = PaymentDetailS.model_validate(
        payment, from_attributes=True
    )

    assert payment_to_pydantic == PaymentDetailS(  # check if to payments are equal
        id=payment_id,
        status="success",
        payment_provider="yookassa",
        amount=1000
    )

    order_summary: OrderS = await order_service.get_order_summary(
        session=session,
        payment_id=payment_to_pydantic.id
    )

    assert order_summary.total_sum == 1000

    order_details: ReturnOrderS = await order_service.get_order_details_by_payment_id(
        session=session,
        payment_id=payment_id
    )

    book_ids = []
    for book in order_details.books:
        book_ids.append(book.book_id)

    assert len(book_ids) == 1 and UUID("20aaefdc-ab3b-4074-af87-dc26a36bb6a0") in book_ids



@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def test_perform_order_with_failed_payment(
        order_service: OrderService,
        payment_service: PaymentService,
        session: AsyncSession
):
    payment_id: UUID = uuid.uuid4()

    payment_detail_repo = PaymentDetailRepository()
    domain_model = PaymentDetailS(
        id=payment_id,
        status="pending",
        payment_provider="yookassa",
        amount=1000.0
    )

    await payment_detail_repo.create(
        session=session,
        domain_model=domain_model
    )  # create fake payment

    with pytest.raises(PaymentFailedError) as excval:
        _ = await order_service.perform_order(
            payment_id=payment_id,
            shopping_session_id=UUID("01e1ca73-5dea-46f2-a19b-56b5a7804efc"),
            status="failed",
        )

    assert "Payment was failed." in str(excval.value)

    payment: PaymentDetailS = await payment_service.get_by_id(
        repo=payment_service._payment_detail_repo,
        session=session,
        id=payment_id
    )

    assert payment.status == "failed"
