from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Protocol, TypeVar

__all__ = (
    "OrmEntityRepoInterface"
)

DomainModelDataT = TypeVar("DomainModelDataT", )


class OrmEntityRepoInterface(Protocol):

    async def create(
            self,
            session: AsyncSession,
            domain_model: DomainModelDataT
    ):
        ...

    async def get_all(
            self,
            session: AsyncSession,
            page: int = 0,
            limit: int = 5,
            **filters,
    ):
        ...

    async def update(
            self,
            domain_model: DomainModelDataT,
            instance_id: int | UUID,
            session: AsyncSession,
    ):
        ...

    async def delete(
            self,
            session: AsyncSession,
            instance_id: int,
    ):
        ...

    async def commit(self, session: AsyncSession):
        ...
