from datetime import timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas import CreateCategoryS, ReturnCategoryS, UpdateCategoryS
from application.services import CategoryService
from auth.services.permission_service import PermissionService
from ....utils.cache import cachify
from infrastructure.postgres import db_client

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[ReturnCategoryS])
async def get_all_categories(
    service: CategoryService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_all_categories(session=session)


@router.get(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[ReturnCategoryS] | None,
    dependencies=[Depends(PermissionService.get_admin_permission)],
)
@cachify(ReturnCategoryS, cache_time=timedelta(seconds=10))
async def get_category_by_id(
    category_id: int,
    service: CategoryService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_category_by_id(session=session, id=category_id)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CreateCategoryS,
    service: CategoryService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.create_category(session=session, dto=data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.delete_category(session=session, category_id=category_id)


@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    update_data: UpdateCategoryS,
    service: CategoryService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.update_category(
        session=session, instance_id=category_id, dto=update_data
    )
