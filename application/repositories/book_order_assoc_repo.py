from typing import Protocol, Union

from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.domain_model_schemas import BookOrderAssocS
from core import OrmEntityRepository
from application.models import BookOrderAssoc
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DBError


class BookOrderAssocRepoInterface(Protocol):
    async def create_many(
            self,
            session: AsyncSession,
            domain_models: list[BookOrderAssocS]
    ) -> None:
        ...


CombinedBookOrderAssocRepoInterface = Union[BookOrderAssocRepoInterface, OrmEntityRepoInterface]


class BookOrderAssocRepository(OrmEntityRepository):
    model = BookOrderAssoc

    async def create_many(
            self,
            session: AsyncSession,
            domain_models: list[BookOrderAssocS]
    ) -> None:
        try:
            to_add: list[BookOrderAssoc] = [BookOrderAssoc(
                **obj.model_dump(exclude_unset=True, exclude_none=True)
            ) for obj in domain_models]
        except Exception as e:
            raise DBError(traceback=str(e))

        session.add_all(to_add)
