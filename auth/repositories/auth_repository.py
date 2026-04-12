import re
from dataclasses import dataclass
from datetime import date
from typing import Any, MutableMapping

import asyncpg
from asyncpg import PostgresError, UniqueViolationError
from loguru import logger

from auth.config import auth_conf
from auth.schemas import RoleName
from shared_lib.exceptions import DBError, DuplicateError, NotFoundError, ServerError


@dataclass(slots=True)
class UserRecord:
    id: int
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    gender: str
    role_name: RoleName
    date_of_birth: date | None


class AuthRepository:
    model_name = "User"
    _updatable_fields = {
        "first_name",
        "last_name",
        "gender",
        "email",
        "hashed_password",
        "role_name",
        "date_of_birth",
    }

    @staticmethod
    def _safe_ident(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid SQL identifier: {name}")
        return name

    @property
    def _users_table(self) -> str:
        schema = self._safe_ident(auth_conf.DB_SCHEMA or "public")
        return f"{schema}.users"

    @staticmethod
    def _to_user_record(row: asyncpg.Record) -> UserRecord:
        return UserRecord(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            gender=row["gender"],
            role_name=row["role_name"],
            date_of_birth=row["date_of_birth"],
        )

    async def retrieve_user_by_email(
        self,
        conn: asyncpg.Connection,
        email: str,
        is_login: bool = False,
    ) -> UserRecord:
        query = (
            f"SELECT id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth "
            f"FROM {self._users_table} WHERE email = $1"
        )
        try:
            row = await conn.fetchrow(query, str(email).lower())
        except PostgresError:
            logger.error(
                "Database error while retrieving user by email",
                extra={"email": email},
                exc_info=True,
            )
            raise ServerError("Unable to retrieve data")

        if row and not is_login:
            raise DuplicateError(entity=self.model_name)

        if not row and is_login:
            raise NotFoundError(entity=self.model_name)

        if row is None:
            raise NotFoundError(entity=self.model_name)

        return self._to_user_record(row)

    async def create_user(
        self,
        data: MutableMapping[str, Any],
        conn: asyncpg.Connection,
    ) -> UserRecord:
        _ = await self.retrieve_user_by_email(
            conn=conn,
            email=data["email"],
            is_login=False,
        )

        query = (
            f"INSERT INTO {self._users_table} "
            "(first_name, last_name, gender, email, hashed_password, role_name, date_of_birth) "
            "VALUES ($1, $2, $3, $4, $5, COALESCE($6, 'user'), $7) "
            "RETURNING id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth"
        )

        try:
            row = await conn.fetchrow(
                query,
                data.get("first_name", None),
                data.get("last_name", None),
                data.get("gender", None),
                data.get("email", None),
                data.get("hashed_password", None),
                data.get("role_name", None),
                data.get("date_of_birth", None),
            )
        except UniqueViolationError as e:
            logger.error(f"failed to add user: {e}")
            raise DBError(traceback=str(e))
        except PostgresError:
            logger.error(
                "Database error while creating user",
                extra={"data": data},
                exc_info=True,
            )
            raise DBError("Failed to create user")

        if row is None:
            raise DBError("Failed to create user")

        return self._to_user_record(row)

    async def retrieve_user_by_id(
        self,
        conn: asyncpg.Connection,
        user_id: int,
    ) -> UserRecord:
        query = (
            f"SELECT id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth "
            f"FROM {self._users_table} WHERE id = $1"
        )
        try:
            row = await conn.fetchrow(query, user_id)
        except PostgresError:
            logger.error(
                "Database error while retrieving user by id",
                extra={"user_id": user_id},
                exc_info=True,
            )
            raise ServerError("Unable to retrieve data")

        if row is None:
            raise NotFoundError(entity=self.model_name)
        return self._to_user_record(row)

    async def list_users(
        self,
        conn: asyncpg.Connection,
        page: int,
        limit: int,
    ) -> list[UserRecord]:
        offset = page * limit
        query = (
            "SELECT id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth "
            f"FROM {self._users_table} "
            "ORDER BY id "
            "OFFSET $1 LIMIT $2"
        )
        try:
            rows = await conn.fetch(query, offset, limit)
        except PostgresError:
            logger.error(
                "Database error while listing users",
                extra={"page": page, "limit": limit},
                exc_info=True,
            )
            raise DBError("Failed to list users")

        return [self._to_user_record(row) for row in rows]

    async def update_user(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        data: MutableMapping[str, Any],
    ) -> UserRecord:
        values = {k: v for k, v in data.items() if v is not None}
        if not values:
            return await self.retrieve_user_by_id(conn=conn, user_id=user_id)

        set_parts: list[str] = []
        params: list[Any] = [user_id]
        for idx, (key, value) in enumerate(values.items(), start=2):
            if key not in self._updatable_fields:
                continue
            safe_field = self._safe_ident(key)
            set_parts.append(f"{safe_field} = ${idx}")
            params.append(value)

        if not set_parts:
            return await self.retrieve_user_by_id(conn=conn, user_id=user_id)

        query = (
            f"UPDATE {self._users_table} SET {', '.join(set_parts)} "
            "WHERE id = $1 "
            "RETURNING id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth"
        )
        try:
            row = await conn.fetchrow(query, *params)
        except UniqueViolationError as e:
            raise DBError(traceback=str(e))
        except PostgresError:
            logger.error(
                "Database error while updating user",
                extra={"user_id": user_id, "keys": list(values.keys())},
                exc_info=True,
            )
            raise DBError("Failed to update user")

        if row is None:
            raise NotFoundError(entity=self.model_name)
        return self._to_user_record(row)

    async def delete_user(
        self,
        conn: asyncpg.Connection,
        user_id: int,
    ) -> None:
        query = f"DELETE FROM {self._users_table} WHERE id = $1 RETURNING id"
        try:
            row = await conn.fetchrow(query, user_id)
        except PostgresError:
            logger.error(
                "Database error while deleting user",
                extra={"user_id": user_id},
                exc_info=True,
            )
            raise DBError("Failed to delete user")

        if row is None:
            raise NotFoundError(entity=self.model_name)

    async def assign_role(
        self,
        conn: asyncpg.Connection,
        user_id: int,
        role_name: RoleName,
    ) -> UserRecord:
        query = (
            f"UPDATE {self._users_table} SET role_name = $2 WHERE id = $1 "
            "RETURNING id, first_name, last_name, email, hashed_password, gender, role_name, date_of_birth"
        )
        try:
            row = await conn.fetchrow(query, user_id, role_name)
        except PostgresError:
            logger.error(
                "Database error while assigning role",
                extra={"user_id": user_id, "role_name": role_name},
                exc_info=True,
            )
            raise DBError("Failed to assign role")

        if row is None:
            raise NotFoundError(entity=self.model_name)

        return self._to_user_record(row)
