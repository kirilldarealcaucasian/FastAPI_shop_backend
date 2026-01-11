from typing import Type

from application.models import Category
from core import OrmEntityRepository


class CategoryRepository(OrmEntityRepository):
    @property
    def model(self) -> Type[Category]:
        return Category
