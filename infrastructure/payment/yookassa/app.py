import asyncio
import json
import uuid
from typing import Protocol, TypeAlias

from yookassa import Payment, Configuration, Refund
from uuid import uuid4, UUID

from application.schemas import CreatePaymentS, ReturnPaymentS
from core.config import settings

__all__ = (
    "PaymentProviderInterface",
    "YooKassaPaymentProvider"
)

from core.exceptions import PaymentObjectCreationError, PaymentRetrieveStatusError
from core.payment_mediator.mediator_saver import InstanceMediatorSaver
from core.payment_mediator.payment_events import PaymentEvents
from logger import logger

PaymentID: TypeAlias = str


class PaymentProviderInterface(Protocol):

    def create_payment(
            self,
            payment_data: CreatePaymentS
    ) -> ReturnPaymentS:
        ...

    def get_payment_status(self, payment_id: str) -> str:
        ...

    async def check_payment_status(
            self,
            payment_id: str,
            shopping_session_id: UUID,
    ):
        ...

    async def make_refund(
            self, payment_id: UUID,
            amount: float, description: str
    ):
        ...


class YooKassaPaymentProvider(InstanceMediatorSaver):
    """Interacts with external payment api"""

    Configuration.account_id = settings.YOOCASSA_ACCOUNT_ID
    Configuration.secret_key = settings.YOOCASSA_SECRET_KEY

    def create_payment(
            self,
            payment_data: CreatePaymentS
    ) -> ReturnPaymentS:
        """
        Creates yoocassa Payment object that includes payment_url and payment_id
        """

        idempotancy_key = uuid4()

        try:
            payment = Payment.create(
                {
                    "amount": {
                        "value": payment_data.total_amount,
                        "currency": payment_data.currency
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": "http://127.0.0.1:8000"
                    },
                    "capture": True,
                    "description": payment_data.description,
                    "metadata": {
                    },
                },
                idempotency_key=idempotancy_key
            )  # create Payment object
        except (TypeError, ValueError):
            extra = {
                "payment_data": payment_data
            }
            logger.error(
                "Failed to create payment object",
                exc_info=True, extra=extra
            )
            raise PaymentObjectCreationError()

        payment_data = json.loads(payment.json())

        payment_id = payment_data["id"]
        confirmation_url = payment_data["confirmation"]["confirmation_url"]
        return ReturnPaymentS(
            confirmation_url=confirmation_url,
            payment_id=payment_id
        )

    def get_payment_status(self, payment_id: PaymentID) -> str:
        try:
            payment = json.loads(Payment.find_one(payment_id).json())
            return payment["status"]
        except Exception:
            logger.error(
                "Failed to get payment_status",
                exc_info=True,
                extra={"payment_id": payment_id}
            )
            raise PaymentRetrieveStatusError()

    async def check_payment_status(
            self,
            payment_id: str,
            shopping_session_id: UUID,
    ) -> None:
        """makes requests to the payment provider to get payment status"""
        payment_status = self.get_payment_status(payment_id=payment_id)

        while payment_status == "pending":
            logger.debug("Checking payment status in the background")
            payment_status = self.get_payment_status(payment_id=payment_id)
            await asyncio.sleep(5)  # relinquish control to the event loop for 5 seconds

        payment_id_to_uuid = uuid.UUID(payment_id)

        if payment_status == "succeeded":
            logger.info("Payment succeeded!")
            await self.mediator.notify(
                event=PaymentEvents.PAYMENT_SUCCEEDED.value,
                payment_id=payment_id_to_uuid,
                shopping_session_id=shopping_session_id,
                status="success"
            )  # send event to the mediator so that it started order creation logic

        else:
            extra = {
                "payment_id": payment_id,
                "shopping_session_id": shopping_session_id
            }
            logger.info("Payment failed (was canceled / timed out)!", extra=extra)

            await self.mediator.notify(
                event=PaymentEvents.PAYMENT_FAILED.value,
                payment_id=payment_id_to_uuid,
                shopping_session_id=shopping_session_id,
                status="failed"
            )  # send event to the mediator so that it aborted order creation process

    async def make_refund(
            self, payment_id: UUID,
            amount: float, description: str
    ):
        res = Refund.create(
            {
                "payment_id": payment_id,
                "description": description,
                "amount": {
                    "value": amount,
                    "currency": "RUB"
                },
            }
        )
        print("REFUND RESULT: ", res.json())
