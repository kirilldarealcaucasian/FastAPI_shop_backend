from uuid import UUID

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared_lib.exceptions import NoCookieError, UnauthorizedError
from ..service_providers.cart import get_cart_service
from ..service_providers.shopping_session import get_shopping_session_service
from ..service_providers.user import get_user_service
from ..schemas.response.shopping_session import GetShoppingSessionResponse
from ..schemas.response.user import GetUserResponse
from ..services.cart_service.cart_service import CartService
from ..services.shopping_session_service import ShoppingSessionService
from ..services.user_service import UserService
from .identity import RequestIdentity, get_request_identity
from infrastructure.postgres import db_client


class PermissionService:
    @staticmethod
    def get_admin_permission(
        identity: RequestIdentity = Depends(get_request_identity),
    ) -> bool:
        if identity.role != "admin":
            raise UnauthorizedError(
                detail="You don't have permission to perform this action"
            )
        return True

    async def get_order_permission(
        self,
        order_id: int,
        user_service: UserService = Depends(get_user_service),
        identity: RequestIdentity = Depends(get_request_identity),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
    ) -> int:
        user_id = identity.user_id

        try:
            user: GetUserResponse = await user_service.get_user_by_order_id(
                session=session,
                order_id=order_id,
            )
        except IndexError as e:
            raise UnauthorizedError(
                detail="You don't have permission to access this data"
            ) from e

        if user.id != user_id and identity.role != "admin":
            raise UnauthorizedError(
                detail="You don't have permission to perform this action"
            )
        return user_id

    async def get_cart_permission(
        self,
        shopping_session_id: UUID = Cookie(None),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        shopping_session_service: ShoppingSessionService = Depends(
            get_shopping_session_service
        ),
    ) -> UUID | None:
        if not shopping_session_id:
            raise NoCookieError("No shopping_session_id in the cookie")

        shopping_session: GetShoppingSessionResponse = (
            await shopping_session_service.get_shopping_session_by_id(
                session=session,
                id=shopping_session_id,
            )
        )

        if shopping_session:
            return shopping_session_id
        return None

    async def get_cart_permission_for_user(
        self,
        user_id: int,
        identity: RequestIdentity = Depends(get_request_identity),
        user_service: UserService = Depends(get_user_service),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
    ) -> None:
        if user_id != identity.user_id:
            raise UnauthorizedError(detail="You are not allowed to access this cart")

        _ = await user_service.get_user_by_id(session=session, id=user_id)

    async def get_authorized_permission(
        self,
        shopping_session_id: UUID = Cookie(None),
        identity: RequestIdentity = Depends(get_request_identity),
        user_service: UserService = Depends(get_user_service),
        cart_service: CartService = Depends(get_cart_service),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
    ) -> None:
        user_id = identity.user_id
        _ = await user_service.get_user_by_id(session=session, id=user_id)

        if shopping_session_id:
            await cart_service.get_cart_by_user_id(session=session, user_id=user_id)
