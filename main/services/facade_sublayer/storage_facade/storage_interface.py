from fastapi import UploadFile
from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession


__all__ = ("StorageInterface",)


class StorageInterface(Protocol):
    async def upload_image(
        self, image: UploadFile, instance_id: int | str
    ): ...

    def delete_image(self, image_id: int, image_url: str): ...

    async def delete_instance_with_images(
        self,
        instance_id: str,
        session: AsyncSession,
        delete_images: bool = False,
    ): ...
