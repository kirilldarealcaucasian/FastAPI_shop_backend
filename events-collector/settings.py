from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "LOCAL"] = "DEV"
    LOG_LEVEL: str = "INFO"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    KAFKA_HOST: str = "localhost"
    KAFKA_PORT: int = 9092
    KAFKA_EVENTS_TOPIC: str = "book_events"

    EVENTS_HISTORY_LIMIT: int = 200
    DB_URL: str | None = None
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "proj_db"

    @property
    def postgres_dsn(self) -> str:
        if self.DB_URL:
            return self.DB_URL.replace("postgresql+asyncpg://", "postgresql://")
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
