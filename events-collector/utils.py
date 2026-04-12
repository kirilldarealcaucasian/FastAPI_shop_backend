import jwt
from shared_lib import RedisConnector
from typing import TYPE_CHECKING

from .settings import Settings

if TYPE_CHECKING:
    from .cmd import BookEventRequest


def build_redis_user_events_key(payload: "BookEventRequest", settings: Settings) -> str:
    if payload.user_id is not None:
        return f"{settings.REDIS_EVENTS_KEY_PREFIX}:user:{payload.user_id}"
    return f"{settings.REDIS_EVENTS_KEY_PREFIX}:session:{payload.session_id}"


async def store_event_in_redis(
    payload: "BookEventRequest",
    redis_connector: RedisConnector,
    settings: Settings,
) -> None:
    redis = await redis_connector.get_redis_connection_dependency()
    if redis is None:
        return

    key = build_redis_user_events_key(payload=payload, settings=settings)
    event_payload = payload.model_dump_json(exclude_none=True)
    pipeline = redis.pipeline(transaction=False)
    pipeline.lpush(key, event_payload)
    pipeline.ltrim(key, 0, settings.REDIS_EVENTS_PER_USER_LIMIT - 1)
    pipeline.expire(key, settings.REDIS_EVENTS_TTL_SECONDS)
    await pipeline.execute()


def extract_user_id_from_jwt(
    jwt_token: str | None,
    settings: Settings,
) -> int | None:
    if jwt_token is None or not jwt_token.strip():
        return None

    decoded_payload = jwt.decode(
        jwt=jwt_token.strip(),
        key=settings.jwt_public_key,
        algorithms=[settings.JWT_DECODE_ALGORITHM],
    )
    user_id = decoded_payload.get("user_id")
    if user_id is None:
        return None
    return int(user_id)


def resolve_session_id(
    payload_session_id: str | None,
    cookie_session_id: str | None,
) -> str | None:
    if payload_session_id is not None and payload_session_id.strip():
        return payload_session_id
    if cookie_session_id is not None and cookie_session_id.strip():
        return cookie_session_id
    return None


__all__ = (
    "build_redis_user_events_key",
    "extract_user_id_from_jwt",
    "resolve_session_id",
    "store_event_in_redis",
)
