from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.request.user import LoginUserRequest, RegisterUserRequest
from application.schemas.response.user import (
    AuthenticatedUserResponse,
    GetUserResponse,
)
from ..schemas import AuthResponse
from ..services.auth_service import AuthService
from infrastructure.postgres import db_client

router = APIRouter(prefix="/v1/auth", tags=['Authentication and Authorization'])
http_bearer = HTTPBearer()


@router.post('/register',
             status_code=status.HTTP_200_OK,
             response_model=GetUserResponse
             )
async def register_user(
        data: RegisterUserRequest,
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        service: AuthService = Depends()
):
    return await service.register_user(session=session, data=data)


@router.post('/login',
             status_code=status.HTTP_200_OK,
             response_model=AuthResponse)
async def login_user(
        creds: LoginUserRequest,
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        service: AuthService = Depends()
):
    return await service.authorize_user(session=session, user_creds=creds)


@router.get('/me', response_model=AuthenticatedUserResponse)
async def get_currently_authed_user(
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency),
        service: AuthService = Depends(),
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return await service.get_auth_user(session=session, credentials=credentials)
