import asyncpg
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from auth.schemas import LoginUserRequest, RegisterUserRequest
from auth.schemas import (
    AssignRoleRequest,
    AuthenticatedUserResponse,
    GetUserResponse,
)
from shared_lib.exceptions import (
    AlreadyExistsError,
    DuplicateError,
    EntityDoesNotExist,
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

    async def register_user(
        self,
        conn: asyncpg.Connection,
        data: RegisterUserRequest,
    ) -> GetUserResponse:
        payload_copy: dict = data.model_copy().model_dump()
        hashed_password = helpers.hash_password(payload_copy["password"])
        del payload_copy["confirm_password"]
        del payload_copy["password"]

        payload_copy["hashed_password"] = hashed_password

        try:
            user = await self._auth_repo.create_user(
                conn=conn,
                data=payload_copy,
            )
            return GetUserResponse.model_validate(user)
        except DuplicateError:
            raise AlreadyExistsError(entity="User")

    async def authorize_user(
        self,
        conn: asyncpg.Connection,
        user_creds: LoginUserRequest,
    ) -> AuthResponse:
        email = user_creds.email

        try:
            user = await self._auth_repo.retrieve_user_by_email(
                conn=conn,
                email=email,
                is_login=True,
            )
        except NotFoundError:
            raise UnauthorizedError("Invalid login / password")

        if not helpers.validate_password(
            password=user_creds.password,
            hashed_password=user.hashed_password,
        ):
            raise UnauthorizedError(detail="Invalid login / password")

        token_payload = TokenPayload(
            user_id=user.id, email=user.email, role=user.role_name
        )

        access_token = helpers.issue_token(
            data=token_payload,
            is_refresh=False,
        )
        refresh_token = helpers.issue_token(
            data=token_payload,
            is_refresh=True,
        )

        return AuthResponse(
            access_token=access_token.token,
            refresh_token=refresh_token.token,
        )

    async def get_auth_user(
        self,
        conn: asyncpg.Connection,
        credentials: HTTPAuthorizationCredentials,
    ) -> AuthenticatedUserResponse:
        payload: dict = get_token_payload(credentials=credentials)
        email: str = validate_token(payload)

        user = await self._auth_repo.retrieve_user_by_email(
            conn=conn,
            email=email,
            is_login=True,
        )

        return AuthenticatedUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_name=user.role_name,
        )

    async def assign_role(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        data: AssignRoleRequest,
    ) -> GetUserResponse:
        try:
            user = await self._auth_repo.assign_role(
                conn=conn,
                user_id=user_id,
                role_name=data.role_name,
            )
            return GetUserResponse.model_validate(user)
        except NotFoundError as e:
            raise EntityDoesNotExist(entity=e.entity)
