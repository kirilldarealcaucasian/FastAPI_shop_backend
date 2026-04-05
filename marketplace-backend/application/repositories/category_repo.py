from typing import Type

from ..models import Category
from .orm_entity_repo import OrmEntityRepository


class CategoryRepository(OrmEntityRepository):
    @property
    def model(self) -> Type[Category]:
        return Category
