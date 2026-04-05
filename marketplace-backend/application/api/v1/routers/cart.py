from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ....schemas.request.cart import AddBookToCartRequest, DeleteBookFromCartRequest
from ....schemas.response.cart import GetCartResponse
from ....services.cart_service.cart_service import CartService
from ....access_control.identity import get_request_identity, RequestIdentity
from ....access_control.permission_service import PermissionService
from infrastructure.postgres import db_client
from ....service_providers.cart import get_cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission)],
    response_model=GetCartResponse,
)
async def get_cart_by_session_id(
    shopping_session_id: Optional[UUID] = Cookie(None),
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    if not shopping_session_id:
        raise HTTPException(status_code=400, detail="no session id in the request")
    return await service.get_cart_by_session_id(
        session=session, shopping_session_id=shopping_session_id
    )


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission_for_user)],
    response_model=GetCartResponse,
)
async def get_cart_by_user_id(
    user_id: int,
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_cart_by_user_id(session=session, user_id=user_id)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def create_cart(
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
    identity: RequestIdentity = Depends(get_request_identity),
):
    return await service.create_cart(session=session, user_id=identity.user_id)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionService().get_cart_permission)],
)
async def delete_cart(
    cart_session_id: UUID = Cookie(None),
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.delete_cart(session=session, cart_session_id=cart_session_id)


@router.post(
    "/items",
    dependencies=[Depends(PermissionService().get_cart_permission)],
    status_code=status.HTTP_200_OK,
)
async def add_book_to_cart(
    data: AddBookToCartRequest,
    shopping_session_id: UUID = Cookie(None),
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.add_book_to_cart(
        session=session, dto=data, shopping_session_id=shopping_session_id
    )


@router.delete(
    "/items",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission)],
)
async def delete_book_from_cart(
    deletion_data: DeleteBookFromCartRequest,
    shopping_session_id: UUID = Cookie(None),
    service: CartService = Depends(get_cart_service),
    session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
) -> GetCartResponse:
    return await service.delete_book_from_cart(
        session=session,
        deletion_data=deletion_data,
        shopping_session_id=shopping_session_id,
    )
