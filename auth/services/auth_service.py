from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import User
from application.schemas.request.user import LoginUserRequest, RegisterUserRequest
from application.schemas.response.user import (
    AuthenticatedUserResponse,
    GetUserResponse,
)
from application.exceptions import (
    AlreadyExistsError,
    DuplicateError,
    NotFoundError,
    UnauthorizedError,
)
from .. import helpers
from ..helpers import get_token_payload, validate_token
from ..repositories import AuthRepository
from ..schemas.token_schema import AuthResponse, TokenPayload


class AuthService:

    def __init__(self, repository: AuthRepository = Depends(AuthRepository)):
        self._auth_repo = repository

    async def register_user(self, session: AsyncSession, data: RegisterUserRequest):
        payload_copy: dict = data.model_copy().model_dump()
        hashed_password = helpers.hash_password(payload_copy["password"])
        del payload_copy["confirm_password"]
        del payload_copy["password"]

        payload_copy["hashed_password"] = hashed_password

        try:
            user: GetUserResponse = await self._auth_repo.create_user(
                session=session,
                data=payload_copy
            )
            return user
        except DuplicateError as e:
            if isinstance(e, DuplicateError):
                raise AlreadyExistsError(entity="User")

    async def authorize_user(
            self,
            session: AsyncSession,
            user_creds: LoginUserRequest
    ) -> AuthResponse:
        email = user_creds.email

        try:
            user = await self._auth_repo.retrieve_user_by_email(
                session=session,
                email=email,
                is_login=True
            )
        except NotFoundError:
            raise UnauthorizedError("Invalid login / password")

        if not helpers.validate_password(
                password=user_creds.password,
                hashed_password=user.hashed_password
        ):
            raise UnauthorizedError(
                detail="Invalid login / password"
            )

        token_payload = TokenPayload(user_id=user.id, email=user.email, role=user.role_name)

        access_token = helpers.issue_token(
            data=token_payload,
            is_refresh=False
        )
        refresh_token = helpers.issue_token(
            data=token_payload,
            is_refresh=True
        )

        return AuthResponse(
            access_token=access_token.token,
            refresh_token=refresh_token.token
        )

    async def get_auth_user(
            self,
            session: AsyncSession,
            credentials: HTTPAuthorizationCredentials
    ) -> AuthenticatedUserResponse:
        payload: dict = get_token_payload(credentials=credentials)
        email: str = validate_token(payload)

        user: User = await self._auth_repo.retrieve_user_by_email(
            session=session,
            email=email, is_login=True
        )

        return AuthenticatedUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_name=user.role_name
        )
