from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.book_repo import CombinedBookRepoInterface
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import EntityDoesNotExist, DomainModelConversionError
from application import CreateBookS, Book
from application.schemas import (
    ReturnImageS,
    ReturnBookS,
    UpdateBookS,
    UpdatePartiallyBookS, BookIdS,
)

from application.repositories import BookRepository, ImageRepository
from application.services.storage import StorageServiceInterface
from application.services.storage.internal_storage import InternalStorageService
from typing import Annotated
from application.schemas.domain_model_schemas import BookS
from pydantic import ValidationError, PydanticSchemaGenerationError
from application.services.utils.filters import BookFilter, Pagination
from logger import logger


class BookService(EntityBaseService):
    def __init__(
            self,
            storage: Annotated[StorageServiceInterface, Depends(InternalStorageService)],
            # you can inject 1 of 2 storage implementations (look application/services/storage)
            book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
            image_repo: Annotated[
                OrmEntityRepoInterface, Depends(ImageRepository)
            ],
    ):
        self.book_repo = book_repo
        self.image_repo = image_repo
        super().__init__(book_repo=book_repo, image_repo=image_repo)
        self.storage: StorageServiceInterface = storage

    async def get_book_by_id(
            self,
            session: AsyncSession,
            id: UUID
    ) -> ReturnBookS:
        book: Book = await super().get_by_id(
            session=session,
            repo=self.book_repo,
            id=str(id)
        )

        genre_names = [category.name for category in book.categories]
        authors = [", ".join(
            [author.first_name, author.last_name]) for author in book.authors]

        return ReturnBookS(
            id=str(book.id),
            name=book.name,
            description=book.description,
            price_per_unit=book.price_per_unit,
            number_in_stock=book.number_in_stock,
            isbn=book.isbn,
            genre_names=genre_names,
            authors=authors,
            rating=book.rating,
            discount=book.discount
        )

    async def get_all_books(
            self,
            session: AsyncSession,
            filters: BookFilter,
            pagination: Pagination
    ) -> list[ReturnBookS]:
        books: list[Book] = await self.book_repo.get_all_books(
            session=session,
            filters=filters,
            pagination=pagination
           )
        res: list[ReturnBookS] = []

        for book in books:
            genre_names = [category.name for category in book.categories]
            authors = [", ".join(
                [author.first_name, author.last_name]) for author in book.authors]

            res.append(ReturnBookS(
                id=book.id,
                isbn=book.isbn,
                name=book.name,
                genre_names=genre_names,
                authors=authors,
                description=book.description,
                price_per_unit=book.price_per_unit,
                number_in_stock=book.number_in_stock,
                rating=book.rating,
                discount=book.discount
            ))
        return res

    async def create_book(
            self, session: AsyncSession, dto: CreateBookS
    ) -> BookIdS:
        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        try:
            domain_model = BookS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError()

        book_id: UUID = await super().create(
                repo=self.book_repo,
                session=session,
                domain_model=domain_model
            )
        return BookIdS(
            id=book_id
        )

    async def delete_book(
            self,
            session: AsyncSession,
            book_id: str,
    ) -> None:
        try:
            _: list[ReturnImageS] = await super().get_all(
                repo=self.image_repo, session=session, book_id=book_id
            )
        except EntityDoesNotExist:
            return await self.storage.delete_instance_with_images(
                delete_images=False, instance_id=book_id, session=session
            )
        return await self.storage.delete_instance_with_images(
            delete_images=True, instance_id=book_id, session=session
        )

    async def update_book(
            self,
            session: AsyncSession,
            book_id: str | int,
            dto: UpdateBookS | UpdatePartiallyBookS,
    ) -> UpdateBookS:
        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)

        try:
            domain_model = BookS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        updated_book: Book = await super().update(
                repo=self.book_repo,
                session=session,
                instance_id=book_id,
                domain_model=domain_model
            )

        return UpdateBookS(
            isbn=updated_book.isbn,
            description=updated_book.description,
            rating=updated_book.rating,
            discount=updated_book.discount,
            name=updated_book.name,
            price_per_unit=updated_book.price_per_unit,
            number_in_stock=updated_book.number_in_stock
        )
