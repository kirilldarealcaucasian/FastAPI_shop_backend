from pathlib import Path
from typing import Literal

from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv("../.env"))

AUTH_DIR = Path(__file__).parent.parent.resolve()


class AuthConfig(BaseSettings):
    MODE: Literal["DEV", "TEST", "LOCAL"] = "DEV"

    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SCHEMA: str | None = Field(default="auth")
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "proj_db"

    TEST_POSTGRES_USER: str = "postgres"
    TEST_POSTGRES_PASSWORD: str = "postgres"
    TEST_POSTGRES_SERVER: str = "localhost"
    TEST_POSTGRES_PORT: int = 5432
    TEST_POSTGRES_DB: str = "proj_db"

    LOCAL_POSTGRES_USER: str = "postgres"
    LOCAL_POSTGRES_PASSWORD: str = "postgres"
    LOCAL_POSTGRES_SERVER: str = "localhost"
    LOCAL_POSTGRES_PORT: int = 5432
    LOCAL_POSTGRES_DB: str = "shop_local"

    ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ENCODE_ALGORITHM: str = "RS256"
    JWT_DECODE_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY: Path = AUTH_DIR / Path("certs") / Path("jwt_public_key.pem")
    JWT_PRIVATE_KEY: Path = AUTH_DIR / Path("certs") / Path("jwt_private_key.pem")
    SALT: str = "test_salt"
    KAFKA_HOST: str = "localhost"
    KAFKA_PORT: int = 9092
    KAFKA_AUTH_EVENTS_TOPIC: str = "auth_events"
    EVENTS_SESSION_COOKIE_NAME: str = "events_session_id"
    EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 15

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def get_db_url(self) -> str:
        if self.MODE == "DEV":
            return (
                "postgresql://"
                f"{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            )
        if self.MODE == "TEST":
            return (
                "postgresql://"
                f"{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}"
                f"@{self.TEST_POSTGRES_SERVER}:{self.TEST_POSTGRES_PORT}/{self.TEST_POSTGRES_DB}"
            )
        if self.MODE == "LOCAL":
            return (
                "postgresql://"
                f"{self.LOCAL_POSTGRES_USER}:{self.LOCAL_POSTGRES_PASSWORD}"
                f"@{self.LOCAL_POSTGRES_SERVER}:{self.LOCAL_POSTGRES_PORT}/{self.LOCAL_POSTGRES_DB}"
            )
        raise RuntimeError("unexpected mode selected, can't get db url")


auth_conf = AuthConfig()
