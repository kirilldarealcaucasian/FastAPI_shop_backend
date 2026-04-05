import json

import pytest

from application.services.events_collector_service import EventsCollectorService


class DummyResponse:
    def __init__(self, status: int = 202):
        self.status = status

    async def text(self) -> str:
        return "ok"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class DummyClientSession:
    def __init__(self, *_, **__):
        self.requests: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, data: str, headers: dict[str, str]):
        self.requests.append({"url": url, "data": data, "headers": headers})
        return DummyResponse(status=202)


@pytest.mark.asyncio
async def test_collect_book_event_sends_payload_to_standalone_service(monkeypatch):
    session = DummyClientSession()
    monkeypatch.setattr(
        "application.services.events_collector_service.aiohttp.ClientSession",
        lambda *args, **kwargs: session,
    )

    service = EventsCollectorService(
        base_url="http://events-collector:8010",
        timeout_seconds=2.0,
    )

    await service.collect_book_event(
        session_id="session-1",
        user_id=10,
        book_id=123,
        event="view",
        ts=1775398200,
        weight=1.0,
    )

    assert len(session.requests) == 1
    request = session.requests[0]
    assert request["url"] == "http://events-collector:8010/api/v1/events/books"
    assert request["headers"] == {"Content-Type": "application/json"}
    payload = json.loads(request["data"])
    assert payload["session_id"] == "session-1"
    assert payload["user_id"] == 10
    assert payload["book_id"] == 123
    assert payload["event"] == "view"
    assert payload["ts"] == 1775398200
    assert payload["weight"] == 1.0
