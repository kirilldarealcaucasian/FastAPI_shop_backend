import asyncpg
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.schemas import AssignRoleRequest, LoginUserRequest, RegisterUserRequest
from auth.schemas import (
    AuthenticatedUserResponse,
    GetUserResponse,
)
from ..infrastructure import get_transaction_connection
from ..schemas import AuthResponse
from ..services.auth_service import AuthService
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/v1/auth", tags=["Authentication and Authorization"])
http_bearer = HTTPBearer()


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
)
async def register_user(
    data: RegisterUserRequest,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: AuthService = Depends(),
):
    return await service.register_user(conn=conn, data=data)


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=AuthResponse,
)
async def login_user(
    creds: LoginUserRequest,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: AuthService = Depends(),
):
    return await service.authorize_user(conn=conn, user_creds=creds)


@router.get("/me", response_model=AuthenticatedUserResponse)
async def get_currently_authed_user(
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: AuthService = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return await service.get_auth_user(conn=conn, credentials=credentials)


@router.patch(
    "/users/{user_id}/role",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
    dependencies=[Depends(PermissionService.get_admin_permission)],
)
async def appoint_role_to_user(
    user_id: int,
    data: AssignRoleRequest,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: AuthService = Depends(),
):
    return await service.assign_role(conn=conn, user_id=user_id, data=data)
