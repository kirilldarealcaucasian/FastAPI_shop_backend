from application.settings import settings
from shared_lib import RedisConnector

__all__ = ("redis_client",)


redis_client = RedisConnector(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
