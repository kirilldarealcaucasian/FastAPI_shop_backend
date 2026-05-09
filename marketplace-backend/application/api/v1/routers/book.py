from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....filters import BookFilter, Pagination
from ....schemas.request.book import (
    CreateBookRequest,
    UpdateBookRequest,
    UpdatePartiallyBookRequest,
)
from ....schemas.response.book import (
    CreateBookResponse,
    GetBookResponse,
    UpdateBookResponse,
)
from ....services.book_service import BookService
from ....service_providers.book import get_book_service
from ....settings import settings
from ....utils.cache import cachify
from ....utils.session_cookie import prolong_events_session_cookie
from infrastructure.postgres import db_client

router = APIRouter(prefix="/books", tags=["Books"])


@router.get(
    "", status_code=status.HTTP_200_OK, response_model=list[GetBookResponse] | None
)
async def get_all_books(
    response: Response,
    pagination: Pagination = Depends(),
    filters: BookFilter = Depends(),
    service: BookService = Depends(get_book_service),
    events_session_id: str | None = Cookie(
        default=None, alias=settings.EVENTS_SESSION_COOKIE_NAME
    ),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    current_session_id = events_session_id or str(uuid4())
    prolong_events_session_cookie(response=response, session_id=current_session_id)
    return await service.get_all_books(
        session=session, filters=filters, pagination=pagination
    )


@router.get(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetBookResponse,
)
@cachify(GetBookResponse, cache_time=timedelta(seconds=10))
async def get_book_by_id(
    book_id: int,
    response: Response,
    service: BookService = Depends(get_book_service),
    events_session_id: str | None = Cookie(
        default=None, alias=settings.EVENTS_SESSION_COOKIE_NAME
    ),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    current_session_id = events_session_id or str(uuid4())
    prolong_events_session_cookie(response=response, session_id=current_session_id)
    return await service.get_book_by_id(session=session, id=book_id)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=CreateBookResponse
)
async def create_book(
    data: CreateBookRequest,
    service: BookService = Depends(get_book_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.create_book(session=session, dto=data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> None:
    return await service.delete_book(session=session, book_id=book_id)


@router.put("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(
    book_id: int,
    update_data: UpdateBookRequest,
    service: BookService = Depends(get_book_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> UpdateBookResponse:
    return await service.update_book(session=session, book_id=book_id, dto=update_data)


@router.patch("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book_partially(
    book_id: int,
    update_data: UpdatePartiallyBookRequest,
    service: BookService = Depends(get_book_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.update_book(session=session, book_id=book_id, dto=update_data)
