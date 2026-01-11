from typing import TypedDict

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv(".env"))


class Config(TypedDict):
    aws_access_key_id: str
    aws_secret_access_key: str
    endpoint_url: str
    region_name: str


class S3Config(BaseSettings):
    SERVICE_NAME: str
    ENDPOINT_URL: str
    BUCKET_NAME: str
    REGION_NAME: str
    TENANT_ID: str
    KEY_ID: str
    SECRET_KEY: str

    @property
    def get_client_config(cls) -> Config:
        return Config(
            aws_access_key_id=cls.TENANT_ID + ":" + cls.KEY_ID,
            aws_secret_access_key=cls.SECRET_KEY,
            endpoint_url=cls.ENDPOINT_URL,
            region_name=cls.REGION_NAME,
        )

    model_config = SettingsConfigDict(env_file=".env")


S3Conf = S3Config()
