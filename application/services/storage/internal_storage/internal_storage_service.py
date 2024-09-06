import os
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
    # implements functionality for managing storage of images in the application/static/images folder

    def __init__(
            self,
            book_repo: BookRepository = Depends(),
            image_manager: ImageManager = Depends(),
    ):
        self.book_repo = book_repo
        super().__init__(book_repo=book_repo)
        self.__image_manager = image_manager

    async def upload_image(
            self,
            instance_id: str | int,
            image: UploadFile,
    ) -> CreateImageS:
        from application.tasks.tasks1 import upload_image
        res: ImageData = await self.__image_manager(
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

    async def delete_image(self, image_url: str, image_id: int) -> None:
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
            instance_id: str,
            session: AsyncSession,
            delete_images: bool = False,
    ) -> None:
        from application.tasks.tasks1 import delete_all_images
        logger.debug("in delete_instance_with_images")
        if delete_images:
            _ = super().delete(
                    session=session,
                    repo=self.book_repo,
                    instance_id=instance_id
            )  # if no exceptions was raised
            await super().commit(session=session)
            delete_all_images.delay(instance_id)
        else:
            try:
                await super().delete(
                    repo=self.book_repo,
                    session=session,
                    instance_id=instance_id
                )
                await super().commit(session=session)
            except EntityDoesNotExist:
                raise EntityDoesNotExist(entity="Book")

