from contextlib import asynccontextmanager
import time
import sys
import os
from typing import Union, MutableMapping, Any, Mapping

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from aioredis import Redis

from infrastructure.minio import minio_client
from infrastructure.postgres import db_client
from infrastructure.redis import redis_client

from .api.v1 import (
    author_router,
    book_router,
    cart_router,
    payment_router,
    order_router,
    user_router,
)
from .settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_client.connect()
    await redis_client.connect()
    await minio_client.connect()
    yield
    await db_client.disconnect()
    await redis_client.disconnect()
    await minio_client.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    book_router,
    order_router,
    user_router,
    author_router,
    cart_router,
    payment_router,
):
    app.include_router(router)


def render_metadata(record: MutableMapping[str, Any]) -> None:
    extra: Mapping[str, Any] = record.get("extra", {})
    if extra:
        record["kv"] = " ".join(f"{key}={value}" for key, value in extra.items())
    else:
        record["kv"] = ""


logger.configure(
    handlers=[
        {
            "sink": sys.stdout,
            "level": os.getenv("log_level") or "INFO",
            "format": '<level>{level}: fn="{function}" msg="{message}" {kv}</level>',
        }
    ],
    patcher=render_metadata,  # type: ignore
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.exception("something went wrong")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Something went wrong"},
            )
        raise e
    process_time = time.time() - start_time
    logger.info(
        "Request execution time: ",
        extra={"request_process_time": round(process_time, 3)},
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response


if settings.MODE != "TEST":

    @app.middleware("http")
    async def throttle_requests(request: Request, call_next):
        """aborts requests if request_counter >= threshold within time interval"""
        redis_con: Union[Redis, None] = await redis_client.connect()

        if not redis_con:
            return await call_next(request)

        client_ip: str = request.client.host  # type: ignore
        key = ":".join(["throttler", client_ip])

        requests_counter = await redis_con.get(key)

        if not requests_counter:
            await redis_con.set(name=key, value=1, ex=1)

        else:
            if int(requests_counter) >= 10:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Too many requests"},
                    headers={"Retry-After": "10"},
                )
            await redis_con.incr(name=key, amount=1)
        return await call_next(request)


@app.get("/health")
def home():
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("application.cmd:app", reload=True)
