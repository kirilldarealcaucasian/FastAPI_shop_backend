from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv("../.env"))

AUTH_DIR = Path(__file__).parent.parent.resolve()


class AuthConfig(BaseSettings):
    ACCESS_TOKEN_EXPIRES_IN: int
    JWT_ENCODE_ALGORITHM: str
    JWT_DECODE_ALGORITHM: str
    JWT_PUBLIC_KEY: Path = AUTH_DIR / "certs" / "jwt_public_key.pem"
    JWT_PRIVATE_KEY: Path = AUTH_DIR / "certs" / "jwt_private_key.pem"
    SALT: str

    model_config = SettingsConfigDict(env_file=".env")


conf = AuthConfig()



