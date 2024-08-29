from typing import Annotated

from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.domain_model_schemas import PublisherS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from application.repositories import PublisherRepository
from application.schemas import CreatePublisherS, ReturnPublisherS
from core.exceptions import DomainModelConversionError
from logger import logger


class PublisherService(EntityBaseService):
    def __init__(
        self,
        publisher_repo: Annotated[
            OrmEntityRepoInterface, Depends(PublisherRepository)
        ],
    ):
        super().__init__(publisher_repo=publisher_repo)
        self.publisher_repo = publisher_repo

    async def get_all_publishers(self, session: AsyncSession):
        return super().get_all(repo=self.publisher_repo, session=session)

    async def get_publishers_by_filters(
        self, session: AsyncSession, **filters
    ) -> list[ReturnPublisherS]:
        return await super().get_all(
            repo=self.publisher_repo, session=session, **filters
        )

    async def create_publisher(
        self,
        session: AsyncSession,
        dto: CreatePublisherS
    ) -> None:
        dto: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = PublisherS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        await super().create(
            repo=self.publisher_repo,
            session=session,
            domain_model=domain_model
        )

    async def delete_publisher(
        self, session: AsyncSession, publisher_id: int
    ) -> None:
        await super().delete(
            repo=self.publisher_repo, session=session, instance_id=publisher_id
        )
