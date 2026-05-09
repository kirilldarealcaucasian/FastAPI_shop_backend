from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from auth.infrastructure import db_client
from auth.infrastructure.kafka import kafka_connector
from auth.routers import auth_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db_client.connect()
    await kafka_connector.connect()
    yield
    await kafka_connector.disconnect()
    await db_client.disconnect()


app = FastAPI(lifespan=lifespan, docs_url="/api/v1/docs", redoc_url="/api/v1/redoc")
app.mount("/api/v1", app)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "Ok"}


if __name__ == "__main__":
    uvicorn.run("auth.cmd:app", reload=True)
