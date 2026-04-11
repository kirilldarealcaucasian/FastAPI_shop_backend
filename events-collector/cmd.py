from contextlib import asynccontextmanager

import jwt
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from shared_lib import KafkaConnector, KafkaPublisher

from .settings import settings


kafka_connector = KafkaConnector(host=settings.KAFKA_HOST, port=settings.KAFKA_PORT)
kafka_publisher = KafkaPublisher(connector=kafka_connector)


class BookEventRequest(BaseModel):
    session_id: str = Field(min_length=1)
    user_id: int | None = None
    jwt_token: str | None = None
    book_id: int = Field(ge=1)
    event: str = Field(min_length=1, max_length=64)
    ts: int = Field(ge=0)
    weight: float = Field(default=1.0, gt=0)


def _extract_user_id_from_jwt(jwt_token: str | None) -> int | None:
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    await kafka_connector.connect()
    yield
    await kafka_connector.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)


@app.post("/events/collect", status_code=202)
async def collect_book_event(payload: BookEventRequest) -> dict[str, str]:
    message_payload = payload.model_dump(exclude_none=True)
    if message_payload.get("user_id") is None:
        try:
            resolved_user_id = _extract_user_id_from_jwt(payload.jwt_token)
        except (jwt.PyJWTError, TypeError, ValueError):
            resolved_user_id = None
        if resolved_user_id is not None:
            message_payload["user_id"] = resolved_user_id

    await kafka_publisher.send_message(
        topic=settings.KAFKA_EVENTS_TOPIC,
        message=BookEventRequest.model_validate(message_payload)
        .model_dump_json(exclude_none=True)
        .encode("utf-8"),
    )
    return {"status": "accepted"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("events_collector.cmd:app", reload=True, host="0.0.0.0", port=8010)
