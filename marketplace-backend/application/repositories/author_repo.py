from typing import Type

from ..models import Author
from .orm_entity_repo import OrmEntityRepository


class AuthorRepository(OrmEntityRepository[Author]):
    @property
    def model(self) -> Type[Author]:
        return Author
