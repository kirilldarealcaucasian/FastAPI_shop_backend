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
