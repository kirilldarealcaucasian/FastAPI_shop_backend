from fastapi.exceptions import HTTPException


class PaymentObjectCreationError(TypeError):

    def __str__(self):
        return f"Failed create Payment object"


class PaymentRetrieveStatusError(TypeError):
    def __str__(self):
        return f"Failed to get payment status"


class PaymentFailedError(HTTPException):

    def __init__(self, detail: str):
        self.detail = detail

    def __str__(self):
        return self.detail

class RefundFailedError(HTTPException):

    def __init__(self, detail: str):
        self.detail = detail

    def __str__(self):
        return self.detail