from uuid import UUID

from pydantic import BaseModel, Field


class PaymentDetailS(BaseModel):
    id: UUID | None = None
    order_id: int | None = None
    status: str | None = Field(default="pending")
    payment_provider: str | None = None
    amount: float | None = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, PaymentDetailS):
            return False

        conditions = [
            str(self.id) == str(other.id),
            self.order_id == other.order_id,
            self.payment_provider == other.payment_provider,
            self.amount == other.amount
        ]

        if all(conditions):
            return True

        return False