import asyncio

from loguru import logger

from .db import connect_db, disconnect_db
from .s3 import s3_parquet_client
from .scheduler import run_forever


async def run() -> None:
    await connect_db()
    await s3_parquet_client.connect()
    try:
        await run_forever()
    finally:
        await disconnect_db()
        await s3_parquet_client.disconnect()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("training-features-etl stopped")


if __name__ == "__main__":
    main()
