import datetime
from bcrypt import hashpw, checkpw
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from auth.config.auth_config import auth_conf
from datetime import timedelta
from auth.schemas import TokenPayload, Token

import jwt

from core.exceptions import UnauthorizedError


def encode_jwt(
        payload: dict,
        expire_timedelta: timedelta,
        private_key: str = auth_conf.JWT_PRIVATE_KEY.read_text(),
        algorithm: str = auth_conf.JWT_ENCODE_ALGORITHM,

) -> Token:
    payload_copy = payload.copy()
    now = datetime.datetime.utcnow()

    expire = now + expire_timedelta
    payload_copy.update(iat=now, exp=expire)

    token: str = jwt.encode(
        payload=payload_copy,
        key=private_key,
        algorithm=algorithm
    )

    return Token(token=token)


def decode_jwt(
        token: str | bytes,
        algorithm: str = auth_conf.JWT_DECODE_ALGORITHM,
        public_key: str = auth_conf.JWT_PUBLIC_KEY.read_text()
) -> dict:
    try:
        return jwt.decode(jwt=token, algorithms=algorithm, key=public_key)
    except jwt.exceptions.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been expired")


def validate_token(payload: dict):
    email: str = getattr(payload, "sub", None)
    expiration: int = getattr(payload, "exp")
    if not email or not expiration or "role_name" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
            )
    return email


def hash_password(password: str, salt: str = auth_conf.SALT) -> str:
    password_to_bytes = password.encode("utf-8")
    hashed_password = hashpw(password_to_bytes, salt.encode("utf-8"))
    return hashed_password.decode()


def validate_password(password: str, hashed_password: str) -> bool:
    if not (is_password_correct := checkpw(password.encode(), hashed_password.encode())
    ):
        raise HTTPException(
           status_code=status.HTTP_401_UNAUTHORIZED,
           detail="Wrong password"
        )
    return is_password_correct


def get_token_payload(credentials: HTTPAuthorizationCredentials) -> dict:
    token: str = credentials.credentials
    if not token:
        raise UnauthorizedError(
            detail="No token in the header. You are not authorized"
        )
    payload: dict = decode_jwt(token)
    return payload


def issue_token(
        data: TokenPayload,
        is_refresh: bool,
):
    if not is_refresh:
        payload = {
            "sub": data.email,
            "user_id": data.user_id,
            "role": data.role
        }
        expire_timedelta = timedelta(hours=auth_conf.ACCESS_TOKEN_EXPIRE_HOURS)
        token = encode_jwt(
            payload=payload,
            expire_timedelta=expire_timedelta
        )
        return token
    else:
        payload = {
            "sub": data.email,
        }
        expire_timedelta = timedelta(days=auth_conf.REFRESH_TOKEN_EXPIRE_DAYS)
        token = encode_jwt(
            payload=payload,
            expire_timedelta=expire_timedelta
        )
        return token


