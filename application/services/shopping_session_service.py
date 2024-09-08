from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import ShoppingSession
from application.repositories import ShoppingSessionRepository
from application.repositories.shopping_session_repo import CombinedShoppingSessionRepositoryInterface
from application.schemas import ReturnShoppingSessionS, CreateShoppingSessionS, ShoppingSessionIdS, \
    UpdatePartiallyShoppingSessionS
from core import EntityBaseService
from application.schemas.domain_model_schemas import ShoppingSessionS
from pydantic import ValidationError, PydanticSchemaGenerationError

from core.config import settings
from core.exceptions import DomainModelConversionError, DBError, NotFoundError, ServerError, EntityDoesNotExist
from logger import logger


class ShoppingSessionService(EntityBaseService):
    def __init__(
            self,
            shopping_session_repo: Annotated[
                CombinedShoppingSessionRepositoryInterface, Depends(ShoppingSessionRepository)]
    ):
        super().__init__(shopping_session_repo=shopping_session_repo)
        self._shopping_session_repo: CombinedShoppingSessionRepositoryInterface = shopping_session_repo

    async def get_shopping_session_by_id(
            self,
            session: AsyncSession,
            id: UUID
    ) -> ReturnShoppingSessionS:
        shopping_session: ShoppingSession = await super().get_by_id(
            session=session,
            repo=self._shopping_session_repo,
            id=id
        )
        logger.debug("ShoppingSession: ", extra={"shopping_session: ": shopping_session})
        return ReturnShoppingSessionS(
            id=shopping_session.id,
            user_id=shopping_session.user_id,
            total=shopping_session.total,
            expiration_time=shopping_session.expiration_time
        )

    async def get_shopping_session_by_id_with_details(
            self,
            session: AsyncSession,
            id: UUID
    ) -> ShoppingSession:
        try:
            return await self._shopping_session_repo.get_shopping_session_with_details(
                session=session,
                id=id
            )
        except (DBError, NotFoundError) as e:
            if type(e) == DBError:
                logger.error(
                    "Failed to get shopping session",
                    extra={"session_id": id},
                    exc_info=True
                )
                raise ServerError()
            elif type(e) == NotFoundError:
                raise EntityDoesNotExist("Cart (books in the cart)")

    async def create_shopping_session(
            self,
            session: AsyncSession,
            dto: CreateShoppingSessionS
    ) -> ShoppingSessionIdS:
        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)

        try:
            domain_model = ShoppingSessionS(**dto)
            domain_model.expiration_time = datetime.now() + settings.SHOPPING_SESSION_EXPIRATION_TIMEDELTA
        except (ValidationError, PydanticSchemaGenerationError):
            extra = {"dto": dto}
            logger.error("failed to convert to domain model", extra, exc_info=True)
            raise DomainModelConversionError

        session_id = await super().create(
            session=session,
            repo=self._shopping_session_repo,
            domain_model=domain_model
        )

        await super().commit(session=session)

        return ShoppingSessionIdS(
            session_id=session_id
        )

    async def update_shopping_session(
            self,
            session: AsyncSession,
            id: str | int,
            dto: UpdatePartiallyShoppingSessionS
    ) -> ReturnShoppingSessionS:
        dto: dict = dto.model_dump(exclude_unset=True)

        try:
            domain_model = ShoppingSessionS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            extra = {"dto": dto}
            logger.error("failed to convert to domain model", extra, exc_info=True)
            raise DomainModelConversionError

        return await super().update(
            session=session,
            repo=self._shopping_session_repo,
            instance_id=id,
            domain_model=domain_model
        )
