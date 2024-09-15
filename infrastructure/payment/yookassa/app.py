import asyncio
import json
from typing import Protocol, TypeAlias, Annotated

from fastapi import Depends
from yookassa import Payment, Configuration, Refund
from uuid import uuid4, UUID

from application.schemas import CreatePaymentS, ReturnPaymentS
from core.config import settings

__all__ = (
    "PaymentProviderInterface",
    "YooKassaPaymentProvider"
)

from core.exceptions import PaymentObjectCreationError, PaymentRetrieveStatusError, PaymentFailedError, \
    RefundFailedError
from logger import logger
from application.services.order_service.order_service import OrderService

PaymentID: TypeAlias = UUID


class PaymentProviderInterface(Protocol):

    def create_payment(
            self,
            payment_data: CreatePaymentS
    ) -> ReturnPaymentS:
        ...

    def get_payment_status(self, payment_id: PaymentID) -> str:
        ...

    async def check_payment_status(
            self,
            payment_id: UUID,
            shopping_session_id: UUID,
            amount: float,
    ):
        ...

    async def make_refund(
            self, payment_id: UUID,
            amount: float, description: str
    ):
        ...


class YooKassaPaymentProvider:
    """Interacts with external payment api"""

    def __init__(
            self,
            order_service: Annotated[OrderService, Depends(OrderService)]
    ):
        self._order_service = order_service

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
            payment = json.loads(Payment.find_one(str(payment_id)).json())
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
            payment_id: UUID,
            shopping_session_id: UUID,
            amount: float,
    ) -> None:
        """makes requests to the payment provider to get payment status"""
        payment_status = self.get_payment_status(payment_id=payment_id)

        while payment_status == "pending":
            logger.debug("Checking payment status in the background")
            payment_status = self.get_payment_status(payment_id=payment_id)
            await asyncio.sleep(5)  # relinquish control to the event loop for 5 seconds

        extra = {
            "payment_id": payment_id,
            "shopping_session_id": shopping_session_id
        }

        if payment_status == "succeeded":
            logger.info("Response from payment provider: payment succeeded")
            try:
                await self._order_service.perform_order(
                    payment_id=payment_id,
                    shopping_session_id=shopping_session_id,
                    status="success"
                )
            except PaymentFailedError as e:
                logger.info("something went wrong, making refund . . .")
                # make refund
                self.make_refund(
                    payment_id=payment_id,
                    amount=amount,
                    description=str(e)
                )
                logger.info("refund has been performed")

        else:
            logger.info("Payment failed (was canceled / timed out)!", extra=extra)
            try:
                await self._order_service.perform_order(
                    payment_id=payment_id,
                    shopping_session_id=shopping_session_id,
                    status="failed"
                )
            except Exception as e:
                logger.error("failed to process canceled payment")

    def make_refund(
            self, payment_id: UUID,
            amount: float, description: str
    ):
        try:
            Refund.create(
                {
                    "payment_id": payment_id,
                    "description": description,
                    "amount": {
                        "value": amount,
                        "currency": "RUB"
                    },
                }
            )
        except Exception:
            extra = {
                "payment_id": payment_id,
                "amount": amount,
                "description": description
            }
            logger.error("failed to make refund", exc_info=True, extra=extra)
            raise RefundFailedError(detail="Failed to make refund")

