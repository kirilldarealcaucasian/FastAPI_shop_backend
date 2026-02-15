from uuid import UUID

from pydantic import BaseModel


class CreatePaymentResponse(BaseModel):
    confirmation_url: str
    payment_id: UUID
