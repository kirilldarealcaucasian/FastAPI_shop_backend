from datetime import timedelta
from fastapi import Depends, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.filters import PaginationS
from application.services import (
    UserService
)
from infrastructure.postgres import db_client

from application.schemas import (UpdateUserS,
                                 UpdatePartiallyUserS,
                                 ReturnUserS, ReturnUserWithOrdersS
                                 )
from auth.services.permission_service import PermissionService
from core.utils.cache import cachify


router = APIRouter(prefix="/v1/users", tags=["Users"])


@router.get("/", status_code=status.HTTP_200_OK,
            response_model=list[ReturnUserS] | None,
            )
async def get_all_users(
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        pagination: PaginationS = Depends()
):
    return await service.get_all_users(session=session, pagination=pagination)


@router.get("/{user_id}",
            status_code=status.HTTP_200_OK,
            response_model=ReturnUserS,
            dependencies=[Depends(PermissionService.get_admin_permission)])
@cachify(ReturnUserS, cache_time=timedelta(seconds=10))
async def get_user_by_id(
        user_id: int,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_user_by_id(session=session, id=user_id)


@router.get(
    "/{user_id}/orders", status_code=status.HTTP_200_OK,
    response_model=ReturnUserWithOrdersS
)
async def get_user_with_orders(
        user_id: int,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_user_with_orders(session=session, user_id=user_id)


@router.get(
    "/{order_id}/orders", status_code=status.HTTP_200_OK,
    response_model=ReturnUserS
)
async def get_user_by_order_id(
        order_id: int,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_user_by_order_id(session=session, order_id=order_id)


@router.delete('/{user_id}',
               status_code=status.HTTP_204_NO_CONTENT,
               response_model=None,
               dependencies=[Depends(PermissionService.get_admin_permission)]
               )
async def delete_user(
        user_id: int,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.delete_user(session=session, user_id=user_id)


@router.put('/{user_id}', dependencies=[Depends(PermissionService.get_admin_permission)])
async def update_user(
        user_id: int,
        update_data: UpdateUserS,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.update_user(
        session=session,
        user_id=user_id,
        dto=update_data
    )


@router.patch('/{user_id}', dependencies=[Depends(PermissionService.get_admin_permission)])
async def update_user_partially(
        user_id: int,
        update_data: UpdatePartiallyUserS,
        service: UserService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.update_user(
        session=session,
        user_id=user_id,
        dto=update_data
    )
