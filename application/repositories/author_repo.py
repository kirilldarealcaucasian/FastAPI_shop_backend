from typing import Type

from application.models import Author
from core import OrmEntityRepository


class AuthorRepository(OrmEntityRepository[Author]):
    @property
    def model(self) -> Type[Author]:
        return Author
