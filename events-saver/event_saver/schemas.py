from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

EventType = Literal["view", "long_view", "cart", "purchase"]


class BookInteractionEvent(BaseModel):
    actor_id: int | None = None
    session_id: UUID | None = None
    book_id: int
    event: EventType
    ts: int
    weight: float = 1.0

    def to_record(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "session_id": self.session_id,
            "item_id": self.book_id,
            "event_type": self.event,
            "event_weight": self.weight,
            "event_timestamp": datetime.fromtimestamp(self.ts),
        }
