from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.postgres import db_client
from application.schemas import CreateOrderS, ReturnOrderS, ShortenedReturnOrderS,\
    UpdatePartiallyOrderS, AddBookToOrderS
from application.schemas.filters import PaginationS
from application.services import OrderService
from core.utils.cache import cachify
from auth.services.permission_service import PermissionService

router = APIRouter(prefix="/v1/orders", tags=["Orders"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[ShortenedReturnOrderS])
async def get_all_orders(
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        pagination: PaginationS = Depends()
):
    return await service.get_all_orders(session=session, pagination=pagination)


@router.get("/{order_id}",
            status_code=status.HTTP_200_OK,
            response_model=ReturnOrderS,
            # dependencies=[Depends(PermissionService().get_order_permission)]
            )
@cachify(
    ReturnOrderS,
    cache_time=timedelta(seconds=10),
)
async def get_order_by_id(
        order_id: int,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_order_by_id(session=session, order_id=order_id)


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[ReturnOrderS]
)
async def get_order_by_user_id(
        user_id: int,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_orders_by_user_id(session=session, user_id=user_id)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_order(
        data: CreateOrderS,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.create_order(session=session, dto=data)


@router.delete(
    '/{order_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(PermissionService().get_order_permission)]
)
async def delete_order(
        order_id: int,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.delete_order(session=session, order_id=order_id)


@router.post(
    '/items',
    # dependencies=[Depends(PermissionService().get_order_permission)],
    status_code=status.HTTP_200_OK,
    response_model=ReturnOrderS
)
async def add_book_to_order(
        order_id: int,
        data: AddBookToOrderS,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.add_book_to_order(
        order_id=order_id,
        session=session,
        dto=data
    )


@router.delete(
    "/{order_id}/books/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=ReturnOrderS
)
async def delete_book_from_order(
        order_id: int,
        book_id: UUID,
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        service: OrderService = Depends()
):
    return await service.delete_book_from_order(
        session=session,
        book_id=book_id,
        order_id=order_id
    )


@router.patch(
    "/{order_id}",
    dependencies=[Depends(PermissionService().get_order_permission)]
)
async def update_order(
        order_id: int,
        update_data: UpdatePartiallyOrderS,
        service: OrderService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.update_order(
        session=session,
        order_id=order_id,
        dto=update_data
    )



