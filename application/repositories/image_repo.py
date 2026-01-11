from application.models import Image
from core import OrmEntityRepository


class ImageRepository(OrmEntityRepository):
    model: Image = Image
