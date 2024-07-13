from datetime import timedelta

from fastapi import Depends, status, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from auth.services.permission_service import PermissionService
from core import db_config
from core.utils.cache import cachify
from application.schemas import (
    CreatePublisherS,
    # UpdatePublisherS,
    # UpdatePartiallyPublisherS,
    ReturnPublisherS
)
from application.services import PublisherService

router = APIRouter(prefix="/publishers", tags=["Publishers"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[ReturnPublisherS] | None)
async def get_all_publishers(
        service: PublisherService = Depends(),
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency)
):
    return await service.get_all_publishers(session=session)


@router.get("/{publisher_id}",
            status_code=status.HTTP_200_OK,
            response_model=list[ReturnPublisherS] | None,
            dependencies=[Depends(PermissionService.get_admin_permission)]
            )
@cachify(ReturnPublisherS, cache_time=timedelta(seconds=10))
async def get_publisher_by_id(
        publisher_id: int,
        service: PublisherService = Depends(),
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency),
):
    return await service.get_publishers_by_filters(session=session, publisher_id=publisher_id)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_publisher(
        data: CreatePublisherS,
        service: PublisherService = Depends(),
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency)
):
    return await service.create_publisher(session=session, dto=data)


@router.delete('/{publisher_id}',
               status_code=status.HTTP_204_NO_CONTENT,
               response_model=None,
               )
async def delete_publisher(
        publisher_id: int,
        service: PublisherService = Depends(),
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency)
):
    return await service.delete_publisher(session=session, publisher_id=publisher_id)


# @router.put('/{publisher_id}', status_code=status.HTTP_200_OK)
# async def update_publisher(
#         publisher_id: int,
#         update_data: UpdatePublisherS,
#         service: PublisherService = Depends(),
#         session: AsyncSession = Depends(db_config.get_scoped_session_dependency)
# ):
#     return await service.update(
#         session=session,
#         instance_id=publisher_id,
#         dto=update_data
#     )
#
#
# @router.patch('/{publisher_id}', status_code=status.HTTP_200_OK)
# async def update_publisher_partially(
#         publisher_id: int,
#         update_data: UpdatePartiallyPublisherS,
#         service: PublisherService = Depends(),
#         session: AsyncSession = Depends(db_config.get_scoped_session_dependency)
# ):
#     return await service.update(
#         session=session,
#         instance_id=publisher_id,
#         dto=update_data
#     )