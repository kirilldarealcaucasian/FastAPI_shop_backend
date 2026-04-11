from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str | None = None
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SERVER: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "proj_db"
    DB_SCHEMA: str = Field(default="events")

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "events"
    S3_REGION: str = "us-east-1"
    S3_SECURE: bool = False
    S3_OBJECT_PREFIX: str = "training_features"

    ETL_RUN_AT_UTC: str = "00:15"
    ETL_RUN_ON_STARTUP: bool = True
    ETL_LOOKBACK_DAYS: int = 1
    ETL_BATCH_SIZE: int = 10_000
    ETL_S3_MULTIPART_PART_SIZE_BYTES: int = 8 * 1024 * 1024

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
