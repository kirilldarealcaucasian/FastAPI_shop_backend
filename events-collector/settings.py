from functools import cached_property
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "LOCAL"] = "DEV"
    LOG_LEVEL: str = "INFO"

    KAFKA_HOST: str = "localhost"
    KAFKA_PORT: int = 9092
    KAFKA_EVENTS_TOPIC: str = "book_events"
    JWT_DECODE_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_PATH: Path = Field(
        default=PROJECT_ROOT / "auth" / "certs" / "jwt_public_key.pem"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @cached_property
    def jwt_public_key(self) -> str:
        return self.JWT_PUBLIC_KEY_PATH.read_text(encoding="utf-8")


settings = Settings()
