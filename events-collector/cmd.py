from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from events_collector.api import events_router
from events_collector.dependencies import kafka_connector, redis_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    await redis_client.connect()
    await kafka_connector.connect()
    yield
    await redis_client.disconnect()
    await kafka_connector.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)
app.include_router(events_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("events_collector.cmd:app", reload=True, host="0.0.0.0", port=8010)
