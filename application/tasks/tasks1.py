import asyncio
import io
import os
import shutil

from PIL import Image
from fastapi import HTTPException, status
from core.image_conf import ImageConfig
from email.message import EmailMessage
from application.tasks.email_config.email_config import email_settings
from application.tasks.task_helpers import email_generator, parse_logs_journal
from pathlib import Path

from infrastructure.celery.app import celery
from logger import logger
from infrastructure.mail import MailClient
from infrastructure.rabbitmq import rabbit_publisher
from celery.utils.log import get_task_logger
from application.repositories.cart_repo import CartRepository

task_logger = get_task_logger(__name__)


def create_image_folder(concrete_image_folder_name: str) -> str:
    image_folder_path: str = os.path.join(
        ImageConfig.static_folder_path,
        ImageConfig.images_folder,
        concrete_image_folder_name
    )
    print("IMAGE_FOLDER_PATH: ", image_folder_path)
    try:
        if not Path(image_folder_path).is_dir():
            os.makedirs(image_folder_path, exist_ok=True)
    except OSError:
        extra = {"problem_directory": concrete_image_folder_name}
        logger.error("Os Exception: Unable to create image directory", extra, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while uploading an image"
        )
    return image_folder_path


def fix_and_save_image(image_io: io.BytesIO, full_image_path: str):
    try:
        with Image.open(image_io) as fixed_image:
            width, height = fixed_image.size

            if width > ImageConfig.image_width_bound:
                width = ImageConfig.image_width_bound
                fixed_image = fixed_image.resize((width, height))

            if height > ImageConfig.image_height_bound:
                height = ImageConfig.image_height_bound
                fixed_image = fixed_image.resize((width, height))

            fixed_image.save(full_image_path)

    except (IOError, OSError, Exception) as e:
        extra = {"full_image_path": full_image_path}
        logger.error("Os Error: Error while opening or saving image", extra, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sth went wrong while fixing image, {e}"
            )


@celery.task
def upload_image(
        image_bytes: bytes,
        image_folder_name: str,
        image_name: str,
):
    image_io = io.BytesIO(image_bytes)
    image_folder_path: str = create_image_folder(image_folder_name)
    full_image_path = os.path.join(image_folder_path, image_name)
    fix_and_save_image(image_io=image_io, full_image_path=full_image_path)


@celery.task
def send_order_summary_email(
        order_data: dict,
) -> None:
    email: EmailMessage = email_generator.create_order_confirmation_template(data=order_data)
    mail_client = MailClient(
        host=email_settings.SMTP_HOST,
        user=email_settings.SMTP_USER,
        password=email_settings.SMTP_PASS,
        port=email_settings.SMTP_PORT
    )
    mail_client.send_message(email)


@celery.task
def delete_all_images(concrete_image_folder: int):
    try:
        shutil.rmtree(
            os.path.join(
                ImageConfig.static_folder_path,
                ImageConfig.images_folder,
                str(concrete_image_folder)
            )
        )
    except OSError:
        extra = {"folder_with_images": concrete_image_folder}
        logger.info("OS Exc: Unable to remove folder with images", extra, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while deleting images"
        )


@celery.task
def save_log():
    """parses logs file, encodes data and sends to the queue"""
    logs_bytes: bytes = parse_logs_journal() # noqa
    if logs_bytes == b'':
        logger.info("no logs to save")
        return
    rabbit_publisher.send_message_basic_publish(
            message=logs_bytes,
            routing_key="logs_q"
        )


@celery.task
def remove_expired_carts():
    """clears database from expired carts"""
    cart_repo = CartRepository()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(cart_repo.delete_expired_carts())
