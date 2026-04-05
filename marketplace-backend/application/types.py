from uuid import UUID
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BookOrderPrimaryIdentifier:
    order_id: int
    book_id: int


@dataclass(slots=True, frozen=True)
class CartPrimaryIdentifier:
    book_id: int
    session_id: UUID


type Id = int | UUID | BookOrderPrimaryIdentifier | CartPrimaryIdentifier
