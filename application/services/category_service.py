from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.category_repo import CategoryRepository
from application.schemas.domain_model_schemas import CategoryS
from core import EntityBaseService
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import EntityDoesNotExist, DomainModelConversionError
from application.schemas import (
    ReturnCategoryS, CreateCategoryS, UpdateCategoryS, CategoryId,
)
from typing import Annotated

from logger import logger


class CategoryService(EntityBaseService):
    def __init__(
        self,
        category_repo: Annotated[OrmEntityRepoInterface, Depends(CategoryRepository)],
    ):
        super().__init__(category_repo=category_repo)
        self._category_repo = category_repo

    async def get_all_categories(
        self,
        session: AsyncSession
    ) -> list[ReturnCategoryS]:
        categories = await super().get_all(
            repo=self._category_repo,
            session=session,
            limit=1000,
        )
        if len(categories) == 0:
            raise EntityDoesNotExist("Category")
        return categories

    async def get_category_by_id(
        self,
        session: AsyncSession,
        id: int # noqa
    ) -> ReturnCategoryS:
        category:  ReturnCategoryS | None = await super().get_by_id(
            repo=self._category_repo,
            session=session,
            id=id
        )
        if category is None:
            raise EntityDoesNotExist(entity="Category")
        return category

    async def delete_category(
        self, session: AsyncSession, category_id: int
    ) -> None:
        await super().delete(
            repo=self._category_repo, session=session, instance_id=category_id
        )
        await super().commit(session=session)

    async def create_category(
            self,
            session: AsyncSession,
            dto: CreateCategoryS,
    ):
        dto: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = CategoryS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        id = await super().create(  # noqa
            repo=self._category_repo,
            session=session,
            domain_model=domain_model
        )
        await super().commit(session=session)

        return CategoryId(
            id=id
        )

    async def update_category(
            self,
            session: AsyncSession,
            instance_id: int | str,
            dto: UpdateCategoryS
    ):
        dto: dict = dto.model_dump(exclude_unset=True)
        try:
            domain_model = CategoryS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise DomainModelConversionError

        return await super().update(
            repo=self._category_repo,
            session=session,
            instance_id=instance_id,
            domain_model=domain_model,
        )
