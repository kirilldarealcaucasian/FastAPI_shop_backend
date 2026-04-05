from collections.abc import Sequence
from typing import Protocol, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Book
from ..filters import BookFilter, Pagination
from .orm_entity_repo import OrmEntityRepoInterface, OrmEntityRepository
from ..types import Id
from shared_lib.exceptions import FilterError


class BookRepoInterface(Protocol):
    async def get_all_books(
        self, session: AsyncSession, filters: BookFilter, pagination: Pagination
    ) -> Sequence[Book]: ...

    async def get_by_id(self, session: AsyncSession, id: Id) -> Book | None: ...


class CombinedBookRepoInterface(
    BookRepoInterface,
    OrmEntityRepoInterface,
    Protocol,
):
    pass


class BookRepository(OrmEntityRepository[Book]):
    @property
    def model(self) -> Type[Book]:
        return Book

    async def get_all_books(
        self, session: AsyncSession, filters: BookFilter, pagination: Pagination
    ) -> Sequence[Book]:
        stmt = select(self.model).options(
            selectinload(Book.categories), selectinload(Book.authors)
        )

        if pagination.limit > 200:
            stmt = filters.filter(stmt)
            stmt = (
                filters.sort(stmt)
                .offset(pagination.page * pagination.limit)
                .limit(pagination.limit)
            )
            stmt = stmt.execution_options(
                yield_per=pagination.limit // 10
            )  # get only 10% of records at a time
            try:
                result = await session.stream_scalars(stmt)
            except CompileError as e:
                raise FilterError() from e
            books: list[Book] = []
            async for book in result:
                books.append(book)
            return books

        stmt = select(self.model).options(
            selectinload(Book.categories), selectinload(Book.authors)
        )

        stmt = filters.filter(stmt)
        stmt = (
            filters.sort(stmt)
            .offset(pagination.page * pagination.limit)
            .limit(pagination.limit)
        )

        try:
            books = list((await session.scalars(stmt)).all())
        except CompileError as e:
            raise FilterError() from e

        return books

    async def get_by_id(self, session: AsyncSession, id: UUID) -> Book | None:
        stmt = (
            select(self.model)
            .options(selectinload(Book.categories), selectinload(Book.authors))
            .where(Book.id == str(id))
        )

        return (await session.execute(stmt)).scalar_one_or_none()
