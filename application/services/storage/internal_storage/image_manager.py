import io

from fastapi import HTTPException, status, UploadFile
from datetime import datetime
from core import ImageConfig
from os import path
from typing import TypedDict
from PIL import Image

from core.exceptions import ServerError
from logger import logger


class ImageData(TypedDict):
    image_url: str
    image_name: str


class ImageManager:
    # validates image credentials(size, format) and generates url

    @staticmethod
    async def image_validate(image: UploadFile, image_format) -> bool:
        image_size = len(await image.read())
        validators = [
            image_format in ImageConfig.allowed_formats,
            image_size < 4000000,
        ]
        await image.seek(0)  # change the stream position to the start
        # (because we might want to read the file again)
        if not validators[0]:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="Not acceptable file format",
            )

        elif not validators[1]:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="File size is too big",
                )

        return True if all(validators) else False

    @staticmethod
    def construct_image_url(format: str, image_folder_name: str) -> ImageData:
        image_folder: str = (
            ImageConfig.images_folder
        )  # generic folder where images are stored
        image_identifier: str = datetime.today().strftime(
            "%Y-%d-%m-%S"
        )  # unique identifier of an image
        image_folder_url = path.join(
            image_folder, image_folder_name
        )  # path to image folder (like images/1)
        image_url = (
            path.join(image_folder_url, image_identifier) + f".{format}"
        )  # path to the image (like images/1/2024-08-02-35.jpeg)

        relative_concrete_image_path = path.join(
            ImageConfig.static_folder_path, image_url
        )  # path up to static folder merged with image_url (like static/images/1/2024-08-02-35.jpeg)
        absolute_concrete_image_path = path.abspath(
            relative_concrete_image_path
        )  # absolute path to the merged with static/images/1/2024-08-02-35.jpeg

        return ImageData(
            image_url=absolute_concrete_image_path,
            image_name=image_identifier + f".{format}",
        )

    async def __call__(
        self, image: UploadFile, image_folder_name: str
    ) -> ImageData:
        fmt = image.content_type.split("/")[1]

        try:
            if await self.image_validate(image=image, image_format=fmt):
                return self.construct_image_url(
                    format=fmt, image_folder_name=image_folder_name
                )
        except (IOError, OSError) as e:
            logger.error(f"Error while opening image file: {e}", exc_info=True)
            raise ServerError("Unexpected error occurred while uploading a file")