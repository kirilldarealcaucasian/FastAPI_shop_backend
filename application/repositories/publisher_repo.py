from application.models import Publisher
from core import OrmEntityRepository


class PublisherRepository(OrmEntityRepository):
    model: Publisher = Publisher
