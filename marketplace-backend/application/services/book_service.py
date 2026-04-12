from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Book
from ..schemas.request.book import CreateBookRequest
from ..schemas.request.book import UpdateBookRequest, UpdatePartiallyBookRequest
from ..schemas.response.book import (
    CreateBookResponse,
    GetBookResponse,
    UpdateBookResponse,
)
from ..filters import BookFilter, Pagination
from .entity_base_service import EntityBaseService
from ..repositories.book_repo import CombinedBookRepoInterface
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BookService(EntityBaseService[Book]):
    book_repo: CombinedBookRepoInterface

    async def get_book_by_id(self, session: AsyncSession, id: int) -> GetBookResponse:
        book = await super().get_by_id(session=session, repo=self.book_repo, id=id)
        return GetBookResponse.model_validate(book)

    async def get_all_books(
        self, session: AsyncSession, filters: BookFilter, pagination: Pagination
    ) -> Sequence[GetBookResponse]:
        books = await self.book_repo.get_all_books(
            session=session, filters=filters, pagination=pagination
        )

        return [GetBookResponse.model_validate(book) for book in books]

    async def create_book(
        self, session: AsyncSession, dto: CreateBookRequest
    ) -> CreateBookResponse:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        orm_model = Book(**data)

        created_book = await super().create(
            repo=self.book_repo, session=session, orm_model=orm_model
        )
        await super().commit(session=session)

        return CreateBookResponse(
            id=created_book.id,
            name=created_book.name,
            summary=created_book.summary,
            price_per_unit=created_book.price_per_unit,
            number_in_stock=created_book.number_in_stock,
            isbn=created_book.isbn,
            rating=created_book.rating,
            discount=created_book.discount,
        )

    async def delete_book(
        self,
        session: AsyncSession,
        book_id: int,
    ) -> None:
        return await self.book_repo.delete(session=session, instance_id=book_id)

    async def update_book(
        self,
        session: AsyncSession,
        book_id: int,
        dto: UpdateBookRequest | UpdatePartiallyBookRequest,
    ) -> UpdateBookResponse:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)

        book = Book(**data)
        updated_book: Book = await super().update(
            repo=self.book_repo,
            session=session,
            instance_id=book_id,
            orm_model=book,
        )

        return UpdateBookResponse(
            isbn=updated_book.isbn,
            summary=updated_book.summary,
            rating=updated_book.rating,
            discount=updated_book.discount,
            name=updated_book.name,
            price_per_unit=updated_book.price_per_unit,
            number_in_stock=updated_book.number_in_stock,
        )
