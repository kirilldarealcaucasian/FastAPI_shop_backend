from uuid import UUID

from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Union, Protocol

from application.schemas.domain_model_schemas import BookS
from application.services.utils.filters import BookFilter

from application.services.utils.filters import Pagination
from core import OrmEntityRepository
from core.base_repos import OrmEntityRepoInterface
from application.models import Book
from core.exceptions import FilterError
from logger import logger


class BookRepoInterface(Protocol):
    async def get_all_books(
            self,
            session: AsyncSession,
            filters: BookFilter,
            pagination: Pagination
    ) -> list[Book]:
        ...

    async def get_by_id(
            self,
            session: AsyncSession,
            id: UUID4
    ) -> Book:
        pass


CombinedBookRepoInterface = Union[OrmEntityRepoInterface, BookRepoInterface]


class BookRepository(OrmEntityRepository):
    model: Book = Book

    async def get_all_books(
            self,
            session: AsyncSession,
            filters: BookFilter,
            pagination: Pagination
    ) -> list[Book]:
        stmt = select(self.model).options(
            selectinload(Book.categories),
            selectinload(Book.authors)
        )

        if pagination.limit > 1000:
            stmt = select(self.model).options(
                selectinload(Book.categories),
                selectinload(Book.authors)
            )

            stmt = filters.filter(stmt)
            stmt = filters.sort(stmt).offset(
                    pagination.page * pagination.limit
                ).limit(pagination.limit)

            try:
                result = await session.execute(stmt)
            except CompileError:
                raise FilterError()

            books: list[Book] = []

            for chunk in result.yield_per(2):
                books.append(chunk[0])

            logger.debug("books: ", extra={"books": books})
            return books

        stmt = select(self.model).options(
            selectinload(Book.categories),
            selectinload(Book.authors)
        )

        stmt = filters.filter(stmt)
        stmt = filters.sort(stmt).offset(
            pagination.page * pagination.limit
        ).limit(pagination.limit)

        try:
            books = list((await session.scalars(stmt)).all())
        except CompileError:
            raise FilterError()

        logger.debug("books: ", extra={"books": books})
        return books

    async def get_by_id(
            self,
            session: AsyncSession,
            id: UUID
    ) -> Book:
        stmt = select(self.model).options(
            selectinload(Book.categories),
            selectinload(Book.authors)
        ).where(Book.id == str(id))

        return (await session.execute(stmt)).scalar_one_or_none()

