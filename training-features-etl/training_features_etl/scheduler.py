import asyncio
from datetime import UTC, datetime, timedelta

from loguru import logger

from .config import settings
from .db import target_date_window
from .etl import run_once

type Hour = int
type Minute = int


def _parse_schedule_time(raw: str) -> tuple[Hour, Minute]:
    parts = raw.split(":")
    if len(parts) != 2:
        raise ValueError("ETL_RUN_AT_UTC must be in HH:MM format")

    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("ETL_RUN_AT_UTC must be a valid UTC time")
    return hour, minute


def _seconds_until_next_run(now_utc: datetime, hour: Hour, minute: Minute) -> float:
    next_run = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now_utc:
        next_run = next_run + timedelta(days=1)
    return max(1.0, (next_run - now_utc).total_seconds())


async def run_forever() -> None:
    hour, minute = _parse_schedule_time(settings.ETL_RUN_AT_UTC)

    if settings.ETL_RUN_ON_STARTUP:
        target_date, start_dt, end_dt = target_date_window(
            lookback_days=settings.ETL_LOOKBACK_DAYS
        )
        await run_once(target_date=target_date, start_dt=start_dt, end_dt=end_dt)

    while True:
        now_utc = datetime.now(tz=UTC)
        delay = _seconds_until_next_run(now_utc=now_utc, hour=hour, minute=minute)

        logger.info(
            "Next ETL run scheduled",
            extra={
                "run_at_utc": f"{hour:02d}:{minute:02d}",
                "sleep_seconds": int(delay),
            },
        )
        await asyncio.sleep(delay)

        try:
            target_date, start_dt, end_dt = target_date_window(
                lookback_days=settings.ETL_LOOKBACK_DAYS
            )
            await run_once(target_date=target_date, start_dt=start_dt, end_dt=end_dt)
        except Exception:
            logger.exception("Scheduled ETL run failed")
