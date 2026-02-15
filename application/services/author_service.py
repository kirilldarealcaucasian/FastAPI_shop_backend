from loguru import logger
from pydantic import PydanticSchemaGenerationError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas.domain_model_schemas import AuthorS
from .entity_base_service import EntityBaseService
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..exceptions import DomainModelConversionError
from ..schemas.response.author import GetAuthorResponse
from ..schemas.request.author import (
    CreateAuthorRequest,
    UpdateAuthorRequest,
    UpdatePartiallyAuthorRequest,
)


class AuthorService(EntityBaseService):
    def __init__(
        self,
        author_repo: OrmEntityRepoInterface,
    ):
        self._author_repo = author_repo

    async def get_all_authors(self, session: AsyncSession) -> list[GetAuthorResponse]:
        return await super().get_all(
            repo=self._author_repo,
            session=session,
        )

    async def get_authors_by_filters(
        self, session: AsyncSession, **filters
    ) -> list[GetAuthorResponse]:
        return await super().get_all(repo=self._author_repo, session=session, **filters)

    async def create_author(
        self, session: AsyncSession, dto: CreateAuthorRequest
    ) -> None:
        data: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = AuthorS(**data)
        except (ValidationError, PydanticSchemaGenerationError) as e:
            logger.bind(dto=dto).opt(exception=e).error(
                "Failed to generate domain model",
            )
            raise DomainModelConversionError from e

        await super().create(
            repo=self._author_repo, session=session, orm_model=domain_model
        )
        await super().commit(session=session)

    async def delete_author(self, session: AsyncSession, author_id: int) -> None:
        await super().delete(
            repo=self._author_repo, session=session, instance_id=author_id
        )
        await super().commit(session=session)

    async def update_author(
        self,
        author_id: int,
        session: AsyncSession,
        data: UpdatePartiallyAuthorRequest | UpdateAuthorRequest,
    ):
        dto: dict = data.model_dump(exclude_unset=True)
        try:
            domain_model = AuthorS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            extra = {"dto": dto}
            logger.error("failed to convert to domain model", extra, exc_info=True)
            raise DomainModelConversionError

        await super().update(
            repo=self._author_repo,
            session=session,
            domain_model=domain_model,
            instance_id=author_id,
        )
