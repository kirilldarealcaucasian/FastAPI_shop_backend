from typing import Annotated

from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.user_repo import CombinedUserInterface
from application.schemas.domain_model_schemas import UserS
from application.repositories.user_repo import UserRepository
from application.schemas import (
    ReturnUserS,
    UpdateUserS,
    UpdatePartiallyUserS,
    ReturnUserWithOrdersS,
)
from application.schemas.filters import PaginationS
from core.exceptions import EntityDoesNotExist, NotFoundError, ServerError, \
    InvalidModelCredentials
from logger import logger
from core.entity_base_service import EntityBaseService


class UserService(EntityBaseService):
    def __init__(
        self,
        user_repo: Annotated[CombinedUserInterface, Depends(UserRepository)],
    ):
        self._user_repo: CombinedUserInterface = user_repo
        super().__init__(user_repo=user_repo)

    async def get_all_users(
        self, session: AsyncSession, pagination: PaginationS
    ) -> list[ReturnUserS] | ReturnUserS:
        try:
            users = await super().get_all(
                repo=self._user_repo,
                session=session,
                page=pagination.page,
                limit=pagination.limit,
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="User")
        return users

    async def get_user_by_id(
        self,
        session: AsyncSession,
        id: int
    ) -> ReturnUserS:
        try:
            user: ReturnUserS | None = await super().get_by_id(
                repo=self._user_repo,
                session=session,
                id=id
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="User")
        return user

    async def delete_user(
        self, session: AsyncSession, user_id: str | int
    ) -> None:
        await super().delete(
            repo=self._user_repo, session=session, instance_id=user_id
        )
        await super().commit(session=session)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str | int,
        dto: UpdateUserS | UpdatePartiallyUserS,
    ) -> None:
        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        if not dto:
            raise InvalidModelCredentials(message="invalid data")

        try:
            domain_model = UserS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise ServerError()

        return await super().update(
            session=session,
            repo=self._user_repo,
            instance_id=user_id,
            domain_model=domain_model
        )

    async def get_user_with_orders(
        self, session: AsyncSession, user_id: int
    ) -> ReturnUserWithOrdersS:
        return await self._user_repo.get_user_with_orders(
            session=session, user_id=user_id
        )

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> ReturnUserS:
        return await self._user_repo.get_user_by_order_id(
            session=session, order_id=order_id
        )
