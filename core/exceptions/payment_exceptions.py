

class PaymentObjectCreationError(TypeError):

    def __str__(self):
        return f"Failed create Payment object"


class PaymentRetrieveStatusError(TypeError):
    def __str__(self):
        return f"Failed to get payment status"