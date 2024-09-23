import time
from typing import Union

import uvicorn
from aioredis import Redis
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from auth.routers import auth_router
from application.api.rest.v1 import (
    image_router,
    order_router, book_router, user_router,
    publisher_router, author_router,
    cart_router, checkout_router
)
from core.config import settings
from logger import logger
from infrastructure.redis import redis_client


app = FastAPI()

app.add_middleware(
    CORSMiddleware, # noqa
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


for router in (
        book_router, order_router,
        user_router, image_router, auth_router,
        publisher_router, author_router, cart_router,
        checkout_router
):
    app.include_router(router)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(msg="something went wrong", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Something went wrong"},
            )
        raise e
    process_time = time.time() - start_time
    logger.info("Request execution time: ", extra={
        "request_process_time": round(process_time, 3)
    })
    response.headers["X-Process-Time"] = str(process_time)
    return response

if settings.MODE != "TEST":
    @app.middleware("http")
    async def throttle_requests(request: Request, call_next):
        """aborts requests if request_counter >= threshold within time interval"""
        redis_con: Union[Redis, None] = await redis_client.connect()

        if not redis_con:
            return await call_next(request)

        client_ip: str = request.client.host
        key = ":".join(["throttler", client_ip])

        requests_counter = await redis_con.get(key)

        if not requests_counter:
            await redis_con.set(name=key, value=1, ex=1)

        else:
            if int(requests_counter) >= 10:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Too many requests"},
                    headers={"Retry-After": "10"}
                )
            await redis_con.incr(
                name=key,
                amount=1)
        return await call_next(request)


@app.get("/")
def home():
    return {"message": "Heeeeeey!"}


if __name__ == "__main__":
    uvicorn.run("application.cmd:app", reload=True)
