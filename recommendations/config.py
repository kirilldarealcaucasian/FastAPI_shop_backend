from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOOKS_FACTORS_PATH: str = "recommendations/data/books_factors.npy"
    BOOKS_IDS_PATH: str | None = None
    RECOMMENDATIONS_CANDIDATES: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
