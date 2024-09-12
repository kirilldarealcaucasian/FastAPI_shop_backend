from uuid import UUID

from fastapi import APIRouter, Depends, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from application.services import PaymentService
# from application.services.payment_service import ConfirmationURL
from auth.services.permission_service import PermissionService
from infrastructure.postgres import db_client


router = APIRouter(prefix="/v1/checkout", tags=["Checkout"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(PermissionService().get_cart_permission),
        Depends(PermissionService().get_authorized_permission)
    ],
    response_model=None
)
async def make_payment(
        shopping_session_id: UUID = Cookie(),
        service: PaymentService = Depends(PaymentService),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.make_payment(
        session=session,
        shopping_session_id=shopping_session_id
    )
