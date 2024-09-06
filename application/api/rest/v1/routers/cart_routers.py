from typing import Optional

from fastapi import APIRouter, Depends, status, Cookie
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from application.helpers import CustomSecurity
from application.services.cart_service import CartService, get_cart_from_cache
from infrastructure.postgres import db_client
from application.schemas import ReturnCartS, AddBookToCartS, DeleteBookFromCartS
from auth.services.permission_service import PermissionService
from uuid import UUID

router = APIRouter(prefix="/v1/cart", tags=["Cart"])
custom_security = CustomSecurity()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission)],
    response_model=ReturnCartS,
)
@get_cart_from_cache
async def get_cart_by_session_id(
        shopping_session_id: Optional[UUID] = Cookie(None),
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_cart_by_session_id(
        session=session,
        shopping_session_id=shopping_session_id
    )


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission_for_user)],
    response_model=ReturnCartS
)
async def get_cart_by_user_id(
        user_id: int,
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
):
    return await service.get_cart_by_user_id(
        session=session,
        user_id=user_id
    )


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def create_cart(
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(custom_security)
):
    return await service.create_cart(
        session=session,
        credentials=credentials
    )


@router.delete(
    '/',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionService().get_cart_permission)]
)
async def delete_cart(
        cart_session_id: UUID = Cookie(None),
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.delete_cart(
        session=session,
        cart_session_id=cart_session_id
    )


@router.post(
    '/items',
    dependencies=[Depends(PermissionService().get_cart_permission)],
    status_code=status.HTTP_200_OK,
)
async def add_book_to_cart(
        data: AddBookToCartS,
        shopping_session_id: UUID = Cookie(None),
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.add_book_to_cart(
        session=session,
        dto=data,
        shopping_session_id=shopping_session_id
    )


@router.delete(
    "/items",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(PermissionService().get_cart_permission)]
)
async def delete_book_from_cart(
        deletion_data: DeleteBookFromCartS,
        shopping_session_id: UUID = Cookie(None),
        service: CartService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
) -> ReturnCartS:
    return await service.delete_book_from_cart(
        session=session,
        deletion_data=deletion_data,
        shopping_session_id=shopping_session_id
    )


