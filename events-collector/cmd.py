from contextlib import asynccontextmanager
from datetime import datetime

import jwt
import uvicorn
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError
from shared_lib import KafkaConnector, KafkaPublisher, RedisConnector
from shared_lib.recommendations.models import BookEventMessage

from .models import BookEventRequest
from .settings import settings
from .utils import (
    deduce_event_weight,
    extract_jwt_from_authorization_header,
    extract_user_id_from_jwt,
    normalize_event_name,
    resolve_session_id,
    store_event_in_redis,
)

kafka_connector = KafkaConnector(host=settings.KAFKA_HOST, port=settings.KAFKA_PORT)
kafka_publisher = KafkaPublisher(connector=kafka_connector)
redis_connector = RedisConnector(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


def _parse_session_expiration_time(value: str | None) -> datetime:
    if value is None or not value.strip():
        raise HTTPException(
            status_code=422,
            detail=f"{settings.EVENTS_SESSION_EXPIRATION_HEADER_NAME} header is required",
        )
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"{settings.EVENTS_SESSION_EXPIRATION_HEADER_NAME} header "
                "must be ISO datetime"
            ),
        ) from exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    await kafka_connector.connect()
    await redis_connector.connect()
    yield
    await redis_connector.disconnect()
    await kafka_connector.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        settings.EVENTS_SESSION_EXPIRATION_HEADER_NAME,
    ],
)


@app.post("/events/collect", status_code=202)
async def collect_book_event(
    request: Request,
    payload: BookEventRequest,
    events_session_id: str | None = Cookie(
        default=None,
        alias=settings.EVENTS_SESSION_COOKIE_NAME,
    ),
    redis: Redis | None = Depends(redis_connector.get_redis_connection_dependency),
):
    resolved_session_id = resolve_session_id(
        cookie_session_id=events_session_id,
    )
    if resolved_session_id is None:
        raise HTTPException(status_code=422, detail="session_id is required")
    try:
        resolved_user_id = extract_user_id_from_jwt(
            jwt_token=extract_jwt_from_authorization_header(
                request.headers.get("Authorization")
            ),
            settings=settings,
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=403, detail=str(e))

    message_payload = {
        "user_id": resolved_user_id,
        "session_id": resolved_session_id,
        "session_expiration_time": _parse_session_expiration_time(
            request.headers.get(settings.EVENTS_SESSION_EXPIRATION_HEADER_NAME)
        ),
        "book_id": payload.book_id,
        "event": normalize_event_name(payload.action),
        "ts": payload.ts,
        "weight": deduce_event_weight(payload.action),
    }

    event_payload = BookEventMessage.model_validate(message_payload)
    try:
        await store_event_in_redis(
            payload=event_payload,
            settings=settings,
            redis=redis,
        )
    except (RedisError, OSError) as exc:
        # Keep event ingestion available even if Redis is temporarily unavailable.
        logger.opt(exception=exc).warning("failed to persist event to redis")

    await kafka_publisher.send_message(
        topic=settings.KAFKA_EVENTS_TOPIC,
        message=event_payload.model_dump_json(exclude_none=True).encode("utf-8"),
    )
    return JSONResponse(
        content={"status": "accepted"},
        status_code=200,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("events_collector.cmd:app", reload=True, host="0.0.0.0", port=8010)
