import asyncpg
from datetime import datetime, timedelta
from fastapi import APIRouter, Cookie, Depends, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from uuid import UUID

from auth.schemas import (
    AssignRoleRequest,
    LoginUserRequest,
    RegisterUserRequest,
    UpdatePartiallyUserRequest,
    UpdateUserRequest,
)
from ..config import auth_conf
from shared_lib.recommendations.models import UserSessionLinkMessage
from auth.schemas import (
    AuthenticatedUserResponse,
    GetUserResponse,
)
from ..infrastructure import get_transaction_connection
from ..infrastructure.kafka import kafka_publisher
from ..schemas import AuthResponse
from ..services.auth_service import AuthService
from ..services.permission_service import PermissionService
from ..services.user_service import UserService

router = APIRouter(prefix="/v1/auth", tags=["Authentication and Authorization"])
http_bearer = HTTPBearer()


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
)
async def register_user(
    data: RegisterUserRequest,
    events_session_id: str | None = Cookie(
        default=None,
        alias=auth_conf.EVENTS_SESSION_COOKIE_NAME,
    ),
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: AuthService = Depends(),
):
    registered_user = await service.register_user(conn=conn, data=data)
    if events_session_id is not None:
        try:
            link_message = UserSessionLinkMessage(
                session_id=UUID(events_session_id),
                user_id=registered_user.id,
                session_expiration_time=datetime.now()
                + timedelta(seconds=auth_conf.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS),
            )
            await kafka_publisher.send_message(
                topic=auth_conf.KAFKA_AUTH_EVENTS_TOPIC,
                message=link_message.model_dump_json().encode("utf-8"),
            )
        except ValueError as exc:
            logger.opt(exception=exc).warning("failed to publish user session link")

    return registered_user


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
    return await service.authorize_user(
        conn=conn,
        user_creds=creds,
    )


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


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
)
async def get_user_by_id(
    user_id: int,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: UserService = Depends(),
):
    return await service.get_user_by_id(conn=conn, user_id=user_id)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=list[GetUserResponse],
)
async def get_all_users(
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: UserService = Depends(),
    page: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    return await service.get_all_users(conn=conn, page=page, limit=limit)


@router.put(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
)
async def update_user(
    user_id: int,
    data: UpdateUserRequest,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: UserService = Depends(),
):
    return await service.update_user(conn=conn, user_id=user_id, data=data)


@router.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetUserResponse,
)
async def update_user_partially(
    user_id: int,
    data: UpdatePartiallyUserRequest,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: UserService = Depends(),
):
    return await service.update_user(conn=conn, user_id=user_id, data=data)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    conn: asyncpg.Connection = Depends(get_transaction_connection),
    service: UserService = Depends(),
):
    return await service.delete_user(conn=conn, user_id=user_id)
