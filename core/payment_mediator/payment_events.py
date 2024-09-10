from enum import Enum


class PaymentEvents(Enum):
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    MAKE_REFUND = "make_refund"