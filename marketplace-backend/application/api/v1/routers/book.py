from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from ....services.events_collector_service import EventsCollectorService
from ....service_providers.book import get_book_service
from ....service_providers.events_collector import get_events_collector_service
from ....filters import BookFilter, Pagination
from ....access_control.identity import get_optional_user_id
from ....settings import settings
from ....utils.cache import cachify
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
    if not events_session_id:
        response.set_cookie(
            key=settings.EVENTS_SESSION_COOKIE_NAME,
            value=str(uuid4()),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
            expires=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
        )
    return await service.get_all_books(
        session=session, filters=filters, pagination=pagination
    )


async def collect_book_view_event(
    book_id: int,
    response: Response,
    events_collector: EventsCollectorService = Depends(get_events_collector_service),
    events_session_id: str | None = Cookie(
        default=None, alias=settings.EVENTS_SESSION_COOKIE_NAME
    ),
    user_id: int | None = Depends(get_optional_user_id),
) -> None:
    current_session_id = events_session_id
    if not current_session_id:
        current_session_id = str(uuid4())
        response.set_cookie(
            key=settings.EVENTS_SESSION_COOKIE_NAME,
            value=current_session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
            expires=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
        )

    await events_collector.collect_book_event(
        session_id=current_session_id,
        user_id=user_id,
        book_id=book_id,
        event="view",
        weight=1.0,
    )


@router.get(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetBookResponse,
)
@cachify(GetBookResponse, cache_time=timedelta(seconds=10))
async def get_book_by_id(
    book_id: int,
    service: BookService = Depends(get_book_service),
    _: None = Depends(collect_book_view_event),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
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
