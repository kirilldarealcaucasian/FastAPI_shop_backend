from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Category
from ..schemas.request.category import CreateCategoryRequest, UpdateCategoryRequest
from ..schemas.response.category import CategoryIdResponse, GetCategoryResponse
from .entity_base_service import EntityBaseService
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..exceptions import EntityDoesNotExist
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CategoryService(EntityBaseService):
    category_repo: OrmEntityRepoInterface

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
        return categories

    async def get_category_by_id(
        self, session: AsyncSession, id: int  # noqa
    ) -> GetCategoryResponse:
        category: GetCategoryResponse | None = await super().get_by_id(
            repo=self.category_repo, session=session, id=id
        )
        if category is None:
            raise EntityDoesNotExist(entity="Category")
        return category

    async def delete_category(self, session: AsyncSession, category_id: int) -> None:
        await super().delete(
            repo=self.category_repo, session=session, instance_id=category_id
        )
        await super().commit(session=session)

    async def create_category(
        self,
        session: AsyncSession,
        dto: CreateCategoryRequest,
    ):
        data: dict = dto.model_dump(exclude_unset=True)
        orm_model = Category(**data)

        id = await super().create(  # noqa
            repo=self.category_repo, session=session, orm_model=orm_model
        )
        await super().commit(session=session)

        return CategoryIdResponse(id=id)

    async def update_category(
        self, session: AsyncSession, instance_id: int | str, dto: UpdateCategoryRequest
    ):
        data: dict = dto.model_dump(exclude_unset=True)

        return await super().update(
            repo=self.category_repo,
            session=session,
            instance_id=instance_id,
            orm_model=data,
        )
