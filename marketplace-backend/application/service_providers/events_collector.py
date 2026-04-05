from ..services.events_collector_service import EventsCollectorService
from ..settings import settings


def get_events_collector_service() -> EventsCollectorService:
    return EventsCollectorService(
        base_url=settings.EVENTS_COLLECTOR_BASE_URL,
        timeout_seconds=settings.EVENTS_COLLECTOR_TIMEOUT_SECONDS,
    )
