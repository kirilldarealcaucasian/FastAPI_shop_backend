import asyncpg
from fastapi import Depends

from auth import helpers
from auth.repositories import AuthRepository
from auth.schemas import (
    GetUserResponse,
    UpdatePartiallyUserRequest,
    UpdateUserRequest,
)
from shared_lib.exceptions import DBError, EntityDoesNotExist, NotFoundError, ServerError


class UserService:
    def __init__(self, repository: AuthRepository = Depends(AuthRepository)):
        self._auth_repo = repository

    async def get_user_by_id(
        self,
        conn: asyncpg.Connection,
        user_id: int,
    ) -> GetUserResponse:
        try:
            user = await self._auth_repo.retrieve_user_by_id(conn=conn, user_id=user_id)
        except NotFoundError as e:
            raise EntityDoesNotExist(entity=e.entity)

        return GetUserResponse.model_validate(user)

    async def get_all_users(
        self,
        conn: asyncpg.Connection,
        page: int,
        limit: int,
    ) -> list[GetUserResponse]:
        try:
            users = await self._auth_repo.list_users(conn=conn, page=page, limit=limit)
        except DBError:
            raise ServerError("Unable to retrieve users")

        return [GetUserResponse.model_validate(user) for user in users]

    async def update_user(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        data: UpdateUserRequest | UpdatePartiallyUserRequest,
    ) -> GetUserResponse:
        payload = data.model_dump(exclude_unset=True, exclude_none=True)

        password = payload.pop("password", None)
        if password:
            payload["hashed_password"] = helpers.hash_password(password)

        try:
            updated_user = await self._auth_repo.update_user(
                conn=conn, user_id=user_id, data=payload
            )
        except NotFoundError as e:
            raise EntityDoesNotExist(entity=e.entity)
        except DBError:
            raise ServerError("Unable to update user")

        return GetUserResponse.model_validate(updated_user)

    async def delete_user(
        self,
        conn: asyncpg.Connection,
        user_id: int,
    ) -> None:
        try:
            await self._auth_repo.delete_user(conn=conn, user_id=user_id)
        except NotFoundError as e:
            raise EntityDoesNotExist(entity=e.entity)
        except DBError:
            raise ServerError("Unable to delete user")
