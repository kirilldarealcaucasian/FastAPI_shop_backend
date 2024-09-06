from typing import Annotated
from uuid import UUID

from fastapi import Depends, UploadFile
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.domain_model_schemas import ImageS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import RelatedEntityDoesNotExist, DomainModelConversionError, RemoteBucketDeletionError, \
    DeletionError, ServerError
from application.repositories import ImageRepository
from application.schemas import ReturnImageS, CreateImageS, ReturnBookS
from application.services.book_service import BookService
from application.services.storage import InternalStorageService, StorageServiceInterface
from logger import logger


class ImageService(EntityBaseService):
    def __init__(
        self,
        image_repo: Annotated[
            OrmEntityRepoInterface, Depends(ImageRepository)
        ],
        storage_service: Annotated[StorageServiceInterface, Depends(InternalStorageService)],
        book_service: BookService = Depends(),
    ):
        super().__init__(repository=image_repo)
        self.image_repo = image_repo
        self.book_service = book_service
        self.storage_service = storage_service

    async def get_all_images(
        self, session: AsyncSession, book_id: str | int
    ) -> list[ReturnImageS]:
        return await super().get_all(
            session=session, repo=self.image_repo, book_id=book_id
        )

    async def upload_image(
        self,
        session: AsyncSession,
        book_id: UUID,
        image: UploadFile,
    ):
        book: ReturnBookS | None = await self.book_service.get_book_by_id(
            session=session,
            id=book_id
        )

        if not book:
            raise RelatedEntityDoesNotExist(entity="Book")

        image_data: CreateImageS = await self.storage_service.upload_image(
            image=image, instance_id=book_id
        )
        image_data: dict = image_data.model_dump(exclude_unset=True)

        try:
            domain_model = ImageS(**image_data)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"image_data": image_data},
                exc_info=True
                )
            raise DomainModelConversionError

        if image_data:
            await super().create(
                repo=self.image_repo,
                session=session,
                domain_model=domain_model
            )
            await super().commit(session=session)

    async def delete_image(self, session: AsyncSession, image_id: int) -> None:
        image: list[ReturnImageS] = await super().get_all(
            repo=self.image_repo, session=session, id=image_id
        )

        if not image:
            raise RelatedEntityDoesNotExist("Image")
        image_url: str = image[0].url

        _ = await super().delete(
            repo=self.image_repo, session=session, instance_id=image[0].id
        )  # if no exception was raised

        try:
            await self.storage_service.delete_image(
                image_url=image_url, image_id=image_id
            )
        except (RemoteBucketDeletionError, DeletionError):
            await session.rollback()
            raise ServerError(detail="Something went wrong while deleting")

        await super().commit(session=session)

