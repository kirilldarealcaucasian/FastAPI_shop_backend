from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....services import PaymentService
from ....service_providers.payment import get_payment_service
from auth.services.permission_service import PermissionService
from infrastructure.postgres import db_client

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(PermissionService().get_cart_permission),
        Depends(PermissionService().get_authorized_permission),
    ],
    response_model=None,
)
async def make_payment(
    shopping_session_id: UUID = Cookie(),
    service: PaymentService = Depends(get_payment_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.make_payment(
        session=session, shopping_session_id=shopping_session_id
    )
