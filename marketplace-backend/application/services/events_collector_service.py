import json
from dataclasses import dataclass
from time import time

import aiohttp
from loguru import logger


@dataclass(slots=True)
class EventsCollectorService:
    base_url: str
    timeout_seconds: float = 2.0

    async def collect_book_event(
        self,
        session_id: str,
        book_id: int,
        event: str,
        user_id: int | None = None,
        ts: int | None = None,
        weight: float = 1.0,
    ) -> None:
        timestamp = ts if ts is not None else int(time())
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "book_id": book_id,
            "event": event,
            "ts": timestamp,
            "weight": weight,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session_http:
                async with session_http.post(
                    f"{self.base_url}/api/v1/events/books",
                    data=json.dumps(payload, separators=(",", ":"), default=str),
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status >= 400:
                        body = await response.text()
                        logger.warning(
                            "events collector rejected event",
                            extra={"status_code": response.status, "response_body": body},
                        )
        except aiohttp.ClientError as exc:
            logger.opt(exception=exc).warning("failed to send event to events collector")
