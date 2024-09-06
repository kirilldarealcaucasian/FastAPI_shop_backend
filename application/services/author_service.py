from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.domain_model_schemas import AuthorS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from application.repositories import AuthorRepository
from application.schemas import (
    CreateAuthorS,
    ReturnAuthorS,
    UpdateAuthorS,
    UpdatePartiallyAuthorS,
)
from pydantic import ValidationError, PydanticSchemaGenerationError

from core.exceptions import DomainModelConversionError
from logger import logger


class AuthorService(EntityBaseService):
    def __init__(
        self,
        author_repo: Annotated[
            OrmEntityRepoInterface, Depends(AuthorRepository)
        ],
    ):
        super().__init__(auhor_repo=author_repo)
        self.author_repo = author_repo

    async def get_all_authors(
        self, session: AsyncSession
    ) -> list[ReturnAuthorS]:
        return await super().get_all(
            repo=self.author_repo,
            session=session,
        )

    async def get_authors_by_filters(
        self, session: AsyncSession, **filters
    ) -> list[ReturnAuthorS]:
        return await super().get_all(
            repo=self.author_repo, session=session, **filters
        )

    async def create_author(
        self,
        session: AsyncSession,
        dto: CreateAuthorS
    ) -> None:
        dto: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = AuthorS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        await super().create(repo=self.author_repo, session=session, domain_model=domain_model)
        await super().commit(session=session)

    async def delete_author(
        self, session: AsyncSession, author_id: int
    ) -> None:
        await super().delete(
            repo=self.author_repo, session=session, instance_id=author_id
        )
        await super().commit(session=session)

    async def update_author(
        self,
        author_id: int,
        session: AsyncSession,
        data: UpdateAuthorS | UpdatePartiallyAuthorS,
    ):
        dto: dict = data.model_dump(exclude_unset=True)
        try:
            domain_model = AuthorS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            extra = {"dto": dto}
            logger.error("failed to convert to domain model", extra, exc_info=True)
            raise DomainModelConversionError

        await super().update(
            repo=self.author_repo,
            session=session,
            domain_model=domain_model,
            instance_id=author_id,
        )
