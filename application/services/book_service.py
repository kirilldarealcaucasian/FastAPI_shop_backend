from typing import Annotated
from uuid import UUID

from fastapi import Depends
from loguru import logger
from pydantic import PydanticSchemaGenerationError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import Book
from application.repositories.book_repo import BookRepository
from application.repositories.image_repo import ImageRepository
from application.schemas import (BookIdS, ReturnBookS, ReturnImageS,
                                 UpdateBookS, UpdatePartiallyBookS)
from application.schemas.book_schemas import CreateBookS
from application.schemas.domain_model_schemas import BookS
from application.services.storage import (InternalStorageService,
                                          StorageServiceInterface)
from application.services.utils.filters import BookFilter, Pagination
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DomainModelConversionError, EntityDoesNotExist


class BookService(EntityBaseService):
    from application.repositories.book_repo import CombinedBookRepoInterface

    def __init__(
        self,
        storage: Annotated[StorageServiceInterface, Depends(InternalStorageService)],
        book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
        image_repo: Annotated[OrmEntityRepoInterface, Depends(ImageRepository)],
    ):
        self._book_repo = book_repo
        self._image_repo = image_repo
        self._storage: StorageServiceInterface = storage

    async def get_book_by_id(self, session: AsyncSession, id: UUID) -> ReturnBookS:
        book: Book = await super().get_by_id(
            session=session, repo=self._book_repo, id=str(id)
        )

        categories: list[str] = [category.name for category in book.categories]
        authors: list[str] = [author.name for author in book.authors]

        return ReturnBookS(
            id=book.id,
            name=book.name,
            image=book.image,
            summary=book.summary,
            language=book.language,
            country=book.country,
            publisher=book.publisher,
            price_per_unit=book.price_per_unit,
            categories=categories,
            year_of_publication=book.year_of_publication,
            number_in_stock=book.number_in_stock,
            isbn=book.isbn,
            authors=authors,
            rating=book.rating,
            discount=book.discount,
        )

    async def get_all_books(
        self, session: AsyncSession, filters: BookFilter, pagination: Pagination
    ) -> list[ReturnBookS]:
        books: list[Book] = await self._book_repo.get_all_books(
            session=session, filters=filters, pagination=pagination
        )
        res: list[ReturnBookS] = []

        for book in books:
            res.append(
                ReturnBookS(
                    id=book.id,
                    name=book.name,
                    image=book.image,
                    summary=book.summary,
                    language=book.language,
                    country=book.country,
                    publisher=book.publisher,
                    price_per_unit=book.price_per_unit,
                    categories=[category.name for category in book.categories],
                    year_of_publication=book.year_of_publication,
                    number_in_stock=book.number_in_stock,
                    isbn=book.isbn,
                    authors=[author.name for author in book.authors],
                    rating=book.rating,
                    discount=book.discount,
                )
            )
        return res

    async def create_book(self, session: AsyncSession, dto: CreateBookS) -> BookIdS:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        try:
            domain_model = BookS(**data)
        except (ValidationError, PydanticSchemaGenerationError) as e:
            logger.bind(data=data).error(
                "Failed to generate domain model", exc_info=True
            )
            raise DomainModelConversionError() from e

        book_id: int = await super().create(
            repo=self._book_repo, session=session, domain_model=domain_model
        )

        await super().commit(session=session)
        return BookIdS(id=book_id)

    async def delete_book(
        self,
        session: AsyncSession,
        book_id: str,
    ) -> None:
        try:
            _: list[ReturnImageS] = await super().get_all(
                repo=self._image_repo, session=session, book_id=book_id
            )
        except EntityDoesNotExist:
            return await self._storage.delete_instance_with_images(
                delete_images=False, instance_id=book_id, session=session
            )
        return await self._storage.delete_instance_with_images(
            delete_images=True, instance_id=book_id, session=session
        )

    async def update_book(
        self,
        session: AsyncSession,
        book_id: str | int,
        dto: UpdateBookS | UpdatePartiallyBookS,
    ) -> UpdateBookS:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)

        try:
            domain_model = BookS(**data)
        except (ValidationError, PydanticSchemaGenerationError) as e:
            logger.bind(data=data).error(
                "Failed to generate domain model", exc_info=True
            )
            raise DomainModelConversionError from e

        updated_book: Book = await super().update(
            repo=self._book_repo,
            session=session,
            instance_id=book_id,
            domain_model=domain_model,
        )

        return UpdateBookS(
            isbn=updated_book.isbn,
            summary=updated_book.summary,
            rating=updated_book.rating,
            discount=updated_book.discount,
            name=updated_book.name,
            price_per_unit=updated_book.price_per_unit,
            number_in_stock=updated_book.number_in_stock,
        )
