from collections.abc import Sequence
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Category
from ..schemas.request.category import CreateCategoryRequest, UpdateCategoryRequest
from ..schemas.response.category import CategoryIdResponse, GetCategoryResponse
from .entity_base_service import EntityBaseService
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from shared_lib.exceptions import EntityDoesNotExist
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CategoryService(EntityBaseService[Category]):
    category_repo: OrmEntityRepoInterface[Category]

    async def get_all_categories(
        self, session: AsyncSession
    ) -> Sequence[GetCategoryResponse]:
        categories = await super().get_all(
            repo=self.category_repo,
            session=session,
            limit=1000,
        )
        if len(categories) == 0:
            raise EntityDoesNotExist("Category")
        return [GetCategoryResponse(name=category.name) for category in categories]

    async def get_category_by_id(
        self, session: AsyncSession, id: int  # noqa
    ) -> GetCategoryResponse:
        category = await super().get_by_id(
            repo=self.category_repo, session=session, id=id
        )
        return GetCategoryResponse(name=category.name)

    async def delete_category(self, session: AsyncSession, category_id: int) -> None:
        await super().delete(
            repo=self.category_repo, session=session, instance_id=category_id
        )
        await super().commit(session=session)

    async def create_category(
        self,
        session: AsyncSession,
        dto: CreateCategoryRequest,
    ) -> CategoryIdResponse:
        data: dict = dto.model_dump(exclude_unset=True)
        orm_model = Category(**data)

        category_id = cast(
            int,
            await super().create(  # noqa
                repo=self.category_repo, session=session, orm_model=orm_model
            ),
        )
        await super().commit(session=session)

        return CategoryIdResponse(id=category_id)

    async def update_category(
        self, session: AsyncSession, instance_id: int, dto: UpdateCategoryRequest
    ) -> GetCategoryResponse:
        data: dict = dto.model_dump(exclude_unset=True)

        updated_category = await super().update(
            repo=self.category_repo,
            session=session,
            instance_id=instance_id,
            orm_model=Category(**data),
        )
        return GetCategoryResponse(name=updated_category.name)
