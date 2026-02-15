from typing import Annotated
from fastapi import Depends
from ..repositories.category_repo import CategoryRepository
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..services.category_service import CategoryService


def get_category_service(
    category_repo: Annotated[OrmEntityRepoInterface, Depends(CategoryRepository)],
) -> CategoryService:
    return CategoryService(category_repo=category_repo)
