from datetime import timedelta
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

__all__ = (
    "settings",
)

load_dotenv()


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "LOCAL"]

    LOG_LEVEL: str
    LOGS_JOURNAL_NAME: str

    DB_USER: str
    DB_PASSWORD: str
    DB_SERVER: str
    DB_PORT: int
    DB_NAME: str

    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str
    TEST_POSTGRES_SERVER: str
    TEST_POSTGRES_PORT: int
    TEST_POSTGRES_DB: str

    LOCAL_POSTGRES_USER: str
    LOCAL_POSTGRES_PASSWORD: str
    LOCAL_POSTGRES_SERVER: str
    LOCAL_POSTGRES_PORT: int
    LOCAL_POSTGRES_DB: str

    REDIS_HOST: str
    REDIS_PORT: int

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int

    SHOPPING_SESSION_DURATION: str
    SHOPPING_SESSION_COOKIE_NAME: str

    YOOCASSA_ACCOUNT_ID: int
    YOOCASSA_SECRET_KEY: str

    @property
    def SHOPPING_SESSION_EXPIRATION_TIMEDELTA(self) -> timedelta: # noqa
        time_intervals = self.SHOPPING_SESSION_DURATION.split(":")
        # example: "1:0:0" -> 1 day 0 hours 0 minutes
        return timedelta(
            days=int(time_intervals[0]),
            hours=int(time_intervals[1]),
            minutes=int(time_intervals[2])
        )

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def get_db_url(cls): # noqa
        if cls.MODE == "DEV":
            return f"postgresql+asyncpg://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_SERVER}:{cls.DB_PORT}/{cls.DB_NAME}"

        if cls.MODE == "TEST":
            return f"postgresql+asyncpg://{cls.TEST_POSTGRES_USER}:{cls.TEST_POSTGRES_PASSWORD}@{cls.TEST_POSTGRES_SERVER}:{cls.TEST_POSTGRES_PORT}/{cls.TEST_POSTGRES_DB}"

        if cls.MODE == "LOCAL":
            return f"postgresql+asyncpg://{cls.LOCAL_POSTGRES_USER}:{cls.LOCAL_POSTGRES_PASSWORD}@{cls.LOCAL_POSTGRES_SERVER}:{cls.LOCAL_POSTGRES_PORT}/{cls.LOCAL_POSTGRES_DB}"


settings = Settings()
