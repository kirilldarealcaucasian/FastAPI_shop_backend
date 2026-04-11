from datetime import timedelta
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ("settings",)

load_dotenv()


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "LOCAL"]

    LOG_LEVEL: str

    DB_USER: str
    DB_PASSWORD: str
    DB_SCHEMA: str | None = Field(default="public")
    DB_SERVER: str
    DB_PORT: int
    DB_NAME: str

    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str
    TEST_POSTGRES_SERVER: str
    TEST_POSTGRES_PORT: int
    TEST_POSTGRES_DB: str

    LOCAL_POSTGRES_USER: str = "postgres"
    LOCAL_POSTGRES_PASSWORD: str = "postgres"
    LOCAL_POSTGRES_SERVER: str = "localhost"
    LOCAL_POSTGRES_PORT: int = 5432
    LOCAL_POSTGRES_DB: str = "shop_local"

    REDIS_HOST: str
    REDIS_PORT: int

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int

    EVENTS_SESSION_COOKIE_NAME: str = "events_session_id"
    EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 15
    EVENTS_COLLECTOR_BASE_URL: str = "http://localhost:8010"
    EVENTS_COLLECTOR_TIMEOUT_SECONDS: float = 2.0

    MINIO_ENDPOINT_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_REGION: str = "us-east-1"
    MINIO_EVENTS_BUCKET: str = "events"
    MINIO_SECURE: bool = False

    SHOPPING_SESSION_DURATION: str
    SHOPPING_SESSION_COOKIE_NAME: str

    YOOCASSA_ACCOUNT_ID: str = "1"
    YOOCASSA_SECRET_KEY: str
    @property
    def SHOPPING_SESSION_EXPIRATION_TIMEDELTA(self) -> timedelta:  # noqa
        time_intervals = self.SHOPPING_SESSION_DURATION.split(":")
        # example: "1:0:0" -> 1 day 0 hours 0 minutes
        return timedelta(
            days=int(time_intervals[0]),
            hours=int(time_intervals[1]),
            minutes=int(time_intervals[2]),
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def get_db_url(cls):  # noqa
        if cls.MODE == "DEV":
            return f"postgresql+asyncpg://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_SERVER}:{cls.DB_PORT}/{cls.DB_NAME}"

        if cls.MODE == "TEST":
            return f"postgresql+asyncpg://{cls.TEST_POSTGRES_USER}:{cls.TEST_POSTGRES_PASSWORD}@{cls.TEST_POSTGRES_SERVER}:{cls.TEST_POSTGRES_PORT}/{cls.TEST_POSTGRES_DB}"

        if cls.MODE == "LOCAL":
            return f"postgresql+asyncpg://{cls.LOCAL_POSTGRES_USER}:{cls.LOCAL_POSTGRES_PASSWORD}@{cls.LOCAL_POSTGRES_SERVER}:{cls.LOCAL_POSTGRES_PORT}/{cls.LOCAL_POSTGRES_DB}"
        return None


settings = Settings()  # type: ignore
