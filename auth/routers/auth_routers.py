from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from auth.services.auth_service import AuthService
from main.schemas import RegisterUserS, LoginUserS, ReturnUserS, AuthenticatedUserS
from core import db_config
from auth.schemas.token_schema import AccessToken
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(prefix="/auth", tags=['Authentication and Authorization'])
http_bearer = HTTPBearer()


@router.post('/register',
             status_code=status.HTTP_201_CREATED,
             response_model=ReturnUserS
             )
async def register_user(
        data: RegisterUserS,
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency),
        service: AuthService = Depends()
):
    return await service.register_user(session=session, data=data)


@router.post('/login',
             status_code=status.HTTP_200_OK,
             response_model=AccessToken)
async def login_user(
        creds: LoginUserS,
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency),
        service: AuthService = Depends()
):
    return await service.authorize_user(session=session, user_creds=creds)


@router.get('/me', response_model=AuthenticatedUserS)
async def get_currently_authed_user(
        session: AsyncSession = Depends(db_config.get_scoped_session_dependency),
        service: AuthService = Depends(),
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return await service.get_auth_user(session=session, credentials=credentials)