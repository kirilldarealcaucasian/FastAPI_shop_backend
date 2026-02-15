from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(find_dotenv("../.env"))

AUTH_DIR = Path(__file__).parent.parent.resolve()


class AuthConfig(BaseSettings):
    ACCESS_TOKEN_EXPIRE_HOURS: int = 1
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ENCODE_ALGORITHM: str = "RS256"
    JWT_DECODE_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY: Path = AUTH_DIR / Path("certs") / Path("jwt_public_key.pem")
    JWT_PRIVATE_KEY: Path = AUTH_DIR / Path("certs") / Path("jwt_private_key.pem")
    SALT: str = "test_salt"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


auth_conf = AuthConfig()

