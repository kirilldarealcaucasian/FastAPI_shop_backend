from application.settings import settings
from shared_lib import SqlalchemyPostgresConnector

__all__ = (
    "SqlalchemyPostgresConnector",
    "db_client",
)


db_client = SqlalchemyPostgresConnector(url=settings.get_db_url, echo=False)
