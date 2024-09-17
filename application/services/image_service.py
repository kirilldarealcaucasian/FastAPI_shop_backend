from typing import Annotated
from uuid import UUID

from fastapi import Depends, UploadFile
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import Image
from application.schemas.domain_model_schemas import ImageS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import RelatedEntityDoesNotExist, DomainModelConversionError, RemoteBucketDeletionError, \
    DeletionError, ServerError
from application.repositories.image_repo import ImageRepository
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
        book_service: Annotated[BookService, Depends(BookService)],
    ):
        super().__init__(repository=image_repo)
        self._image_repo = image_repo
        self._book_service = book_service
        self._storage_service = storage_service

    async def get_all_images(
        self, session: AsyncSession, book_id: UUID | int
    ) -> list[ReturnImageS]:
        images: list[Image] = await super().get_all(
            session=session,
            repo=self._image_repo,
            book_id=book_id
        )
        res: list[ReturnImageS] = []
        for image in images:
            res.append(
                ReturnImageS(
                    id=image.id,
                    book_id=str(image.book_id),
                    url=image.url
                )
            )
        return res

    async def upload_image(
        self,
        session: AsyncSession,
        book_id: UUID,
        image: UploadFile,
    ):
        book: ReturnBookS | None = await self._book_service.get_book_by_id(
            session=session,
            id=book_id
        )

        if not book:
            raise RelatedEntityDoesNotExist(entity="Book")

        image_data: CreateImageS = await self._storage_service.upload_image(
            image=image, instance_id=book_id
        )
        if not image_data.book_id or not image_data.url:
            raise ServerError(
                detail="Unable to upload the file now due to server error. Try again later"
            )

        image_data: dict = image_data.model_dump()

        try:
            domain_model = ImageS(**image_data)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"image_data": image_data},
                exc_info=True
                )
            raise DomainModelConversionError()

        if image_data:
            await super().create(
                repo=self._image_repo,
                session=session,
                domain_model=domain_model
            )
            await super().commit(session=session)

    async def delete_image(self, session: AsyncSession, image_id: int) -> None:
        image: list[ReturnImageS] = await super().get_all(
            repo=self._image_repo, session=session, id=image_id
        )

        if not image:
            raise RelatedEntityDoesNotExist("Image")
        image_url: str = image[0].url

        _ = await super().delete(
            repo=self._image_repo, session=session, instance_id=image[0].id
        )  # if no exception was raised

        try:
            self._storage_service.delete_image(
                image_url=image_url, image_id=image_id
            )
        except (RemoteBucketDeletionError, DeletionError):
            await session.rollback()
            raise ServerError(detail="Something went wrong while deleting")

        await super().commit(session=session)
