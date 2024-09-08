import os
from typing import Annotated
from uuid import UUID

from fastapi import UploadFile, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.entity_base_service import EntityBaseService
from application.repositories import BookRepository
from application.services.storage.internal_storage.image_manager import (
    ImageManager,
    ImageData,
)
from application.schemas import CreateImageS
from core.exceptions import EntityDoesNotExist, DeletionError

from logger import logger
from celery.exceptions import TaskError


class InternalStorageService(EntityBaseService):
    """implements functionality for managing storage of images
    in the application/static/images folder"""

    def __init__(
            self,
            book_repo: Annotated[BookRepository, Depends(BookRepository)],
            image_manager: Annotated[ImageManager, Depends(ImageManager)],
    ):
        self._book_repo: BookRepository = book_repo
        super().__init__(book_repo=book_repo)
        self._image_manager: ImageManager = image_manager

    async def upload_image(
            self,
            instance_id: str | int | UUID,
            image: UploadFile,
    ) -> CreateImageS:
        """Stores image in the project folder"""
        from application.tasks.tasks1 import upload_image
        res: ImageData = await self._image_manager(
            image=image, image_folder_name=instance_id
        )

        image_url = res.get("image_url", None)
        image_name = res.get("image_name", None)

        if image_url is None or image_name is None:
            raise HTTPException(
                status_code=500, detail="Unable to upload the file"
            )

        try:
            image_bytes: bytes = await image.read()
            upload_image.delay(
                image_bytes=image_bytes,
                image_folder_name=instance_id,
                image_name=image_name,
            )
        except TaskError:
            extra = {"instance_id": instance_id}
            logger.error(
                "Celery error: error while trying to upload the image",
                extra,
                exc_info=True,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to upload the file",
            )

        return CreateImageS(book_id=instance_id, url=image_url)

    def delete_image(self, image_url: str, image_id: int) -> None:
        """deletes image from the project folder"""
        try:
            image_path = os.path.join(image_url)
            os.remove(image_path)
        except FileNotFoundError:
            extra = {"image_id": image_id, "image_url": image_url}
            logger.error(
                "File deletion Error: Error while trying to delete file",
                extra,
                exc_info=True,
            )
            raise DeletionError(
                entity="Image"
            )

    async def delete_instance_with_images(
            self,
            instance_id: str | UUID | int,
            session: AsyncSession,
            delete_images: bool = False,
    ) -> None:
        from application.tasks.tasks1 import delete_all_images
        logger.debug("in delete_instance_with_images")
        if delete_images:
            logger.debug("Deleting book with images")
            # if an instance has images, and we have to delete everything
            _ = super().delete(
                    session=session,
                    repo=self._book_repo,
                    instance_id=instance_id
            )  # if no exceptions was raised
            await super().commit(session=session)
            logger.debug("Book instance has been successfully deleted from the db")
            delete_all_images.delay(instance_id)
        else:
            # if we only need to delete instance from the db
            try:
                await super().delete(
                    repo=self._book_repo,
                    session=session,
                    instance_id=instance_id
                )
                await super().commit(session=session)
            except EntityDoesNotExist:
                extra = {"instance_id": instance_id}
                logger.debug("Book you want to delete doesn't exist", extra=extra)
                raise EntityDoesNotExist(entity="Book")
