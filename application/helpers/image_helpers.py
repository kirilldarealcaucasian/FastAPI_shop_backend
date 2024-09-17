import os
from fastapi import HTTPException, status, File
from collections import namedtuple
from core.image_conf import ImageConfig
import datetime


def get_image_format(image: File) -> str:
    format: str = image.filename.split(".")[1]

    if format not in ImageConfig.allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Not acceptable image format")
    return format


def construct_url(format: str, name: str):
    image_folder: str = ImageConfig.images_folder
    image_date: str = datetime.datetime.today().strftime("%Y-%d-%m-%S")
    folder_url = os.path.join(image_folder, name)
    image_url = os.path.join(folder_url, image_date) + f".{format}"
    image_name = image_date + f".{format}"
    urls = namedtuple("urls", ["folder_url", "image_url", "image_name"])
    return urls(folder_url, image_url, image_name)


def create_image_folder(concrete_image_folder_name: str) -> str:
    from logger.logg import logger
    image_folder = os.path.join(
        ImageConfig.static_folder_path,
        ImageConfig.images_folder,
        concrete_image_folder_name
    )
    try:
        os.mkdir(image_folder)
    except FileExistsError:
        pass
    except OSError:
        extra = {"image_folder": image_folder}
        logger.error("failed to create image folder", exc_info=True, extra=extra)
    return image_folder
