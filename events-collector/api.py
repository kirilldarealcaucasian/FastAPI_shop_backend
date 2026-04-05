from fastapi import APIRouter, Depends, status

from events_collector.dependencies import get_events_collector_service
from events_collector.events_collector_service import EventsCollectorService
from events_collector.schemas import BookEventRequest

events_router = APIRouter(prefix="/events", tags=["Events"])


@events_router.post("/collect", status_code=status.HTTP_202_ACCEPTED)
async def collect_book_event(
    payload: BookEventRequest,
    service: EventsCollectorService = Depends(get_events_collector_service),
) -> dict[str, str]:
    await service.collect_book_event(event=payload)
    return {"status": "accepted"}
