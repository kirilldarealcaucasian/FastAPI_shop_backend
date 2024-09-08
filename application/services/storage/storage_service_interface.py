from uuid import UUID

from fastapi import UploadFile
from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("StorageServiceInterface",)


class StorageServiceInterface(Protocol):
    async def upload_image(
        self,
        instance_id: int | str | UUID,
        image: UploadFile,
    ): ...


    def delete_image(self, image_url: str, image_id: int, ) -> None:
        ...

    async def delete_instance_with_images(
        self,
        instance_id: str | UUID | int,
        session: AsyncSession,
        delete_images: bool = False,
    ): ...
