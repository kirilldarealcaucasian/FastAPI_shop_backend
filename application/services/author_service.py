from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Author
from .entity_base_service import EntityBaseService
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..schemas.response.author import GetAuthorResponse
from ..schemas.request.author import (
    CreateAuthorRequest,
    UpdateAuthorRequest,
    UpdatePartiallyAuthorRequest,
)
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class AuthorService(EntityBaseService):
    author_repo: OrmEntityRepoInterface

    async def get_all_authors(self, session: AsyncSession) -> Sequence[GetAuthorResponse]:
        return await super().get_all(
            repo=self.author_repo,
            session=session,
        )

    async def get_authors_by_filters(
        self, session: AsyncSession, **filters
    ) -> Sequence[GetAuthorResponse]:
        return await super().get_all(repo=self.author_repo, session=session, **filters)

    async def create_author(
        self, session: AsyncSession, dto: CreateAuthorRequest
    ) -> None:
        data: dict = dto.model_dump(exclude_unset=True)
        orm_model = Author(**data)

        await super().create(
            repo=self.author_repo, session=session, orm_model=orm_model
        )
        await super().commit(session=session)

    async def delete_author(self, session: AsyncSession, author_id: int) -> None:
        await super().delete(
            repo=self.author_repo, session=session, instance_id=author_id
        )
        await super().commit(session=session)

    async def update_author(
        self,
        author_id: int,
        session: AsyncSession,
        data: UpdatePartiallyAuthorRequest | UpdateAuthorRequest,
    ):
        dto: dict = data.model_dump(exclude_unset=True)

        await super().update(
            repo=self.author_repo,
            session=session,
            orm_model=dto,
            instance_id=author_id,
        )
