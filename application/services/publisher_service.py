from typing import Annotated

from fastapi import Depends
from loguru import logger
from pydantic import PydanticSchemaGenerationError, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.publisher_repo import PublisherRepository
from application.schemas import CreatePublisherS, PublisherId, ReturnPublisherS
from application.schemas.domain_model_schemas import PublisherS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DomainModelConversionError


class PublisherService(EntityBaseService):
    def __init__(
        self,
        publisher_repo: Annotated[OrmEntityRepoInterface, Depends(PublisherRepository)],
    ):
        super().__init__(publisher_repo=publisher_repo)
        self._publisher_repo = publisher_repo

    async def get_all_publishers(self, session: AsyncSession):
        return super().get_all(repo=self._publisher_repo, session=session)

    async def get_publishers_by_filters(
        self, session: AsyncSession, **filters
    ) -> list[ReturnPublisherS]:
        return await super().get_all(
            repo=self._publisher_repo, session=session, **filters
        )

    async def create_publisher(
        self, session: AsyncSession, dto: CreatePublisherS
    ) -> PublisherId:
        data: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = PublisherS(**data)
        except (ValidationError, PydanticSchemaGenerationError) as e:
            logger.error(
                "Failed to generate domain model", extra={"data": data}, exc_info=True
            )
            raise DomainModelConversionError from e

        id = await super().create(
            repo=self._publisher_repo, session=session, domain_model=domain_model
        )
        await super().commit(session=session)

        return PublisherId(id=id)

    async def delete_publisher(self, session: AsyncSession, publisher_id: int) -> None:
        await super().delete(
            repo=self._publisher_repo, session=session, instance_id=publisher_id
        )
        await super().commit(session=session)
