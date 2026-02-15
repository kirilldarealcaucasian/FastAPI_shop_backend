from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....schemas.response.author import (
    GetAuthorResponse,
)
from ....schemas.request.author import (
    CreateAuthorRequest,
    UpdateAuthorRequest,
    UpdatePartiallyAuthorRequest,
)
from ....services.author_service import AuthorService
from auth.services.permission_service import PermissionService
from ....utils.cache import cachify
from infrastructure.postgres import db_client
from ....service_providers.author import get_author_service

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get(
    "/", status_code=status.HTTP_200_OK, response_model=list[GetAuthorResponse] | None
)
async def get_all_authors(
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_all_authors(session=session)


@router.get(
    "/{author_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[GetAuthorResponse] | None,
    dependencies=[Depends(PermissionService.get_admin_permission)],
)
@cachify(GetAuthorResponse, cache_time=timedelta(seconds=10))
async def get_author_by_id(
    author_id: int,
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_authors_by_filters(session=session, author_id=author_id)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_author(
    data: CreateAuthorRequest,
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.create_author(session=session, dto=data)


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_author(
    author_id: int,
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.delete_author(session=session, author_id=author_id)


@router.put("/{author_id}", status_code=status.HTTP_200_OK)
async def update_author(
    author_id: int,
    update_data: UpdateAuthorRequest,
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.update_author(
        session=session, author_id=author_id, data=update_data
    )


@router.patch("/{author_id}", status_code=status.HTTP_200_OK)
async def update_author_partially(
    author_id: int,
    update_data: UpdatePartiallyAuthorRequest,
    service: Annotated[AuthorService, Depends(get_author_service)],
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.update_author(
        session=session, author_id=author_id, data=update_data
    )
