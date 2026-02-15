from datetime import datetime
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ShoppingSession
from ..repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
)
from ..schemas.request.shopping_session import (
    CreateShoppingSessionRequest,
    UpdatePartiallyShoppingSessionRequest,
)
from ..schemas.response.shopping_session import GetShoppingSessionResponse
from ..types import Id
from .entity_base_service import EntityBaseService
from ..settings import settings
from ..exceptions import (
    EntityDoesNotExist,
    NotFoundError,
)
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ShoppingSessionService(EntityBaseService):
    shopping_session_repo: CombinedShoppingSessionRepositoryInterface

    async def get_shopping_session_by_id(
        self, session: AsyncSession, id: Id
    ) -> GetShoppingSessionResponse:
        shopping_session: ShoppingSession = await super().get_by_id(
            session=session, repo=self.shopping_session_repo, id=id
        )
        logger.debug(
            "ShoppingSession: ", extra={"shopping_session: ": shopping_session}
        )
        return GetShoppingSessionResponse(
            id=shopping_session.id,
            user_id=shopping_session.user_id,
            total=shopping_session.total,
            expiration_time=shopping_session.expiration_time,
        )

    async def get_shopping_session_by_id_with_details(
        self, session: AsyncSession, id: UUID
    ) -> ShoppingSession:
        try:
            return await self.shopping_session_repo.get_shopping_session_with_details(
                session=session, id=id
            )
        except NotFoundError:
            raise EntityDoesNotExist("Cart not found")

    async def create_shopping_session(
        self, session: AsyncSession, dto: CreateShoppingSessionRequest
    ) -> Id:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        data["expiration_time"] = (
            datetime.now() + settings.SHOPPING_SESSION_EXPIRATION_TIMEDELTA
        )
        orm_model = ShoppingSession(**data)

        session_id = await super().create(
            session=session, repo=self.shopping_session_repo, orm_model=orm_model
        )

        await super().commit(session=session)

        return session_id

    async def update_shopping_session(
        self,
        session: AsyncSession,
        id: UUID,
        dto: UpdatePartiallyShoppingSessionRequest,
    ) -> GetShoppingSessionResponse:
        data: dict = dto.model_dump(exclude_unset=True)

        return await super().update(
            session=session,
            repo=self.shopping_session_repo,
            instance_id=id,
            orm_model=data,
        )
