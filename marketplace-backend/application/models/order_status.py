from enum import Enum


class OrderStatus(str, Enum):
    DONE = "done"
    PENDING = "pending"
    REFUND = "refund"
