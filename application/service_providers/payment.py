from typing import Annotated

from fastapi import Depends

from infrastructure.payment.yookassa.app import (
    PaymentProviderInterface,
    YooKassaPaymentProvider,
)

from ..repositories.cart_repo import CartRepository, CombinedCartRepositoryInterface
from ..repositories.payment_detail_repo import (
    CombinedPaymentDetailRepoInterface,
    PaymentDetailRepository,
)
from ..repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
    ShoppingSessionRepository,
)
from ..services.payment_service import PaymentService


def get_payment_service(
    payment_provider: Annotated[
        PaymentProviderInterface,
        Depends(YooKassaPaymentProvider),
    ],
    shopping_session_repo: Annotated[
        CombinedShoppingSessionRepositoryInterface,
        Depends(ShoppingSessionRepository),
    ],
    cart_repo: Annotated[CombinedCartRepositoryInterface, Depends(CartRepository)],
    payment_detail_repo: Annotated[
        CombinedPaymentDetailRepoInterface,
        Depends(PaymentDetailRepository),
    ],
) -> PaymentService:
    return PaymentService(
        payment_provider=payment_provider,
        shopping_session_repo=shopping_session_repo,
        cart_repo=cart_repo,
        payment_detail_repo=payment_detail_repo,
    )
