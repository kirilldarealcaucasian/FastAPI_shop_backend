from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas import (
    BookIdS,
    CreateBookS,
    ReturnBookS,
    UpdateBookS,
    UpdatePartiallyBookS,
)
from application.services import BookService
from application.services.utils.filters import BookFilter, Pagination
from ....utils.cache import cachify
from infrastructure.postgres import db_client

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", status_code=status.HTTP_200_OK, response_model=list[ReturnBookS] | None)
async def get_all_books(
    pagination: Pagination = Depends(),
    filters: BookFilter = Depends(),
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_all_books(
        session=session, filters=filters, pagination=pagination
    )


@router.get(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=ReturnBookS,
)
@cachify(ReturnBookS, cache_time=timedelta(seconds=10))
async def get_book_by_id(
    book_id: UUID,
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_book_by_id(session=session, id=book_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookIdS)
async def create_book(
    data: CreateBookS,
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.create_book(session=session, dto=data)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> None:
    return await service.delete_book(session=session, book_id=str(book_id))


@router.put("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book(
    book_id: UUID,
    update_data: UpdateBookS,
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> UpdateBookS:
    return await service.update_book(
        session=session, book_id=str(book_id), dto=update_data
    )


@router.patch("/{book_id}", status_code=status.HTTP_200_OK)
async def update_book_partially(
    book_id: UUID,
    update_data: UpdatePartiallyBookS,
    service: BookService = Depends(),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.update_book(
        session=session, book_id=str(book_id), dto=update_data
    )
