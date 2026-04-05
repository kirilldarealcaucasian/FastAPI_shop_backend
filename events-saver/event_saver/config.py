from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "book_events"
    KAFKA_GROUP_ID: str = "event-saver"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    KAFKA_BATCH_SIZE: int = 100

    DB_URL: str | None = None
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "proj_db"
    DB_SCHEMA: str = Field(default="events")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def db_url(self) -> str:
        if self.DB_URL:
            return self.DB_URL.replace("postgresql+asyncpg://", "postgresql://")
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
