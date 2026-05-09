import jwt
from typing import TYPE_CHECKING

from redis.asyncio import Redis
from shared_lib.recommendations.enums import BookEventAction

from .settings import Settings

type SessionId = str
type UserId = int


if TYPE_CHECKING:
    from shared_lib.recommendations.models import BookEventMessage


def _build_redis_user_events_key(
    payload: "BookEventMessage", settings: Settings
) -> str:
    if payload.user_id is not None:
        return f"{settings.REDIS_EVENTS_KEY_PREFIX}:user:{payload.user_id}"
    return f"{settings.REDIS_EVENTS_KEY_PREFIX}:session:{payload.session_id}"


async def store_event_in_redis(
    payload: "BookEventMessage",
    settings: Settings,
    redis: Redis | None,
) -> None:
    if redis is None:
        return

    key = _build_redis_user_events_key(payload=payload, settings=settings)
    event_payload = payload.model_dump_json(exclude_none=True)
    pipeline = redis.pipeline(transaction=False)
    pipeline.lpush(key, event_payload)
    pipeline.ltrim(key, 0, settings.REDIS_EVENTS_PER_USER_LIMIT - 1)
    pipeline.expire(key, settings.REDIS_EVENTS_TTL_SECONDS)
    await pipeline.execute()


def normalize_event_name(event: str) -> str:
    action = BookEventAction.from_action(event)
    if action is None:
        return event.strip().lower().replace("-", "_")
    return action.value


def deduce_event_weight(action: str) -> float:
    event_action = BookEventAction.from_action(action)
    if event_action is None:
        return 1.0
    return event_action.weight


def extract_user_id_from_jwt(
    jwt_token: str | None,
    settings: Settings,
) -> UserId | None:
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


def extract_jwt_from_authorization_header(authorization: str | None) -> str | None:
    if authorization is None or not authorization.strip():
        return None

    value = authorization.strip()
    scheme, separator, token = value.partition(" ")
    if not separator:
        return value
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def resolve_session_id(
    cookie_session_id: str | None,
) -> SessionId | None:
    if cookie_session_id is not None and cookie_session_id.strip():
        return cookie_session_id
    return None


__all__ = (
    "deduce_event_weight",
    "extract_jwt_from_authorization_header",
    "extract_user_id_from_jwt",
    "normalize_event_name",
    "resolve_session_id",
    "store_event_in_redis",
)
