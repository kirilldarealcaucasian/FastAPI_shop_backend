from contextlib import asynccontextmanager

import jwt
import uvicorn
from fastapi import Cookie, FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from shared_lib import KafkaConnector, KafkaPublisher, RedisConnector

from .settings import settings
from .utils import extract_user_id_from_jwt, resolve_session_id, store_event_in_redis


kafka_connector = KafkaConnector(host=settings.KAFKA_HOST, port=settings.KAFKA_PORT)
kafka_publisher = KafkaPublisher(connector=kafka_connector)
redis_connector = RedisConnector(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


class BookEventRequest(BaseModel):
    session_id: str | None = None
    user_id: int | None = None
    jwt_token: str | None = None
    book_id: int = Field(ge=1)
    event: str = Field(min_length=1, max_length=64)
    ts: int = Field(ge=0)
    weight: float = Field(default=1.0, gt=0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await kafka_connector.connect()
    await redis_connector.connect()
    yield
    await redis_connector.disconnect()
    await kafka_connector.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)


@app.post("/events/collect", status_code=202)
async def collect_book_event(
    payload: BookEventRequest,
    events_session_id: str | None = Cookie(
        default=None,
        alias=settings.EVENTS_SESSION_COOKIE_NAME,
    ),
) -> dict[str, str]:
    message_payload = payload.model_dump(exclude_none=True)
    resolved_session_id = resolve_session_id(
        payload_session_id=payload.session_id,
        cookie_session_id=events_session_id,
    )
    if resolved_session_id is None:
        raise HTTPException(status_code=422, detail="session_id is required")
    message_payload["session_id"] = resolved_session_id

    if message_payload.get("user_id") is None:
        try:
            resolved_user_id = extract_user_id_from_jwt(
                jwt_token=payload.jwt_token,
                settings=settings,
            )
        except (jwt.PyJWTError, TypeError, ValueError):
            resolved_user_id = None
        if resolved_user_id is not None:
            message_payload["user_id"] = resolved_user_id

    normalized_payload = BookEventRequest.model_validate(message_payload)
    try:
        await store_event_in_redis(
            payload=normalized_payload,
            redis_connector=redis_connector,
            settings=settings,
        )
    except (RedisError, OSError) as exc:
        # Keep event ingestion available even if Redis is temporarily unavailable.
        logger.opt(exception=exc).warning("failed to persist event to redis")

    await kafka_publisher.send_message(
        topic=settings.KAFKA_EVENTS_TOPIC,
        message=normalized_payload.model_dump_json(exclude_none=True).encode("utf-8"),
    )
    return {"status": "accepted"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("events_collector.cmd:app", reload=True, host="0.0.0.0", port=8010)
