from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import User
from application.schemas import (AuthenticatedUserS, LoginUserS, RegisterUserS,
                                 ReturnUserS)
from auth import helpers
from auth.helpers import get_token_payload, validate_token
from auth.repositories import AuthRepository
from auth.schemas.token_schema import AuthResponse, TokenPayload
from core.exceptions import (AlreadyExistsError, DuplicateError, NotFoundError,
                             UnauthorizedError)


class AuthService:

    def __init__(self, repository: AuthRepository = Depends(AuthRepository)):
        self._auth_repo = repository

    async def register_user(self, session: AsyncSession, data: RegisterUserS):
        payload_copy: dict = data.model_copy().model_dump()
        hashed_password = helpers.hash_password(payload_copy["password"])
        del payload_copy["confirm_password"]
        del payload_copy["password"]

        payload_copy["hashed_password"] = hashed_password

        try:
            user: ReturnUserS = await self._auth_repo.create_user(
                session=session,
                data=payload_copy
            )
            return user
        except DuplicateError as e:
            if type(e) == DuplicateError:
                raise AlreadyExistsError(entity="User")

    async def authorize_user(
            self,
            session: AsyncSession,
            user_creds: LoginUserS
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
    ) -> AuthenticatedUserS:
        payload: dict = get_token_payload(credentials=credentials)
        email: str = validate_token(payload)

        user: User = await self._auth_repo.retrieve_user_by_email(
            session=session,
            email=email, is_login=True
        )

        return AuthenticatedUserS(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_name=user.role_name
        )
