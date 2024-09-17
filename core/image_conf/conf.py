from abc import ABC
import os


class ImageConfig(ABC):
    images_folder: str = "images"
    allowed_formats: list = ["jpeg", "jpg", "gif", "png", "tiff", "bpm"]
    # static_folder_path = os.path.join("application", "static")
    static_folder_path = os.path.join("static")

    image_width_bound: int = 1024
    image_height_bound: int = 1024

