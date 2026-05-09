import asyncio

from loguru import logger

from .consumer import consume_forever
from .db import connect_db, disconnect_db


async def run() -> None:
    logger.info("event-saver starting")
    await connect_db()
    try:
        await consume_forever()
    finally:
        await disconnect_db()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("event-saver stopped")


if __name__ == "__main__":
    main()
