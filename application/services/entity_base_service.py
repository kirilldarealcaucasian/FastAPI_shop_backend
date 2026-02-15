from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Sequence

from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..exceptions import AlreadyExistsError, DuplicateError, ServerError
from ..exceptions.http_exceptions import EntityDoesNotExist
from ..utils import perform_logging
from ..types import Id


class EntityBaseService[OrmModelT]:
    """
    Takes out responsibility of handling exceptions in each of the service classes.
    EntityBaseService calls to the repository defined in each subclass
    of EntityBaseService
    """

    @perform_logging
    async def create(
        self,
        repo: OrmEntityRepoInterface,
        session: AsyncSession,
        orm_model: OrmModelT,
    ) -> OrmModelT:
        try:
            created = await repo.create(orm_model=orm_model, session=session)
            return getattr(created, "id", created)
        except DuplicateError as e:
            raise AlreadyExistsError(e.entity) from e

    @perform_logging
    async def update(
        self,
        repo: OrmEntityRepoInterface,
        session: AsyncSession,
        instance_id: Id,
        orm_model: OrmModelT,
    ) -> OrmModelT:
        instance = await repo.get_by_id(session=session, id=instance_id)
        if instance is None:
            raise EntityDoesNotExist(entity=f"{repo.model}")

        if isinstance(orm_model, dict):
            values = orm_model
        else:
            values = {
                key: value
                for key, value in vars(orm_model).items()
                if not key.startswith("_")
            }

        for key, value in values.items():
            setattr(instance, key, value)

        return await repo.update(
            session=session,
            instance_id=instance_id,
            orm_model=instance,
        )

    @perform_logging
    async def get_all(
        self, repo: OrmEntityRepoInterface, session: AsyncSession, **filters
    ) -> Sequence[OrmModelT]:
        return await repo.get_all(**filters, session=session)

    @perform_logging
    async def get_by_id(
        self,
        session: AsyncSession,
        repo: OrmEntityRepoInterface[OrmModelT],
        id: Id,
    ) -> OrmModelT:
        res = await repo.get_by_id(id=id, session=session)
        if res is None:
            raise EntityDoesNotExist(entity=f"{repo.model}")
        return res

    @perform_logging
    async def delete(
        self,
        repo: OrmEntityRepoInterface,
        session: AsyncSession,
        instance_id: Id,
    ) -> None:
        _ = await repo.delete(instance_id=instance_id, session=session)

    async def commit(self, session: AsyncSession):
        try:
            await session.commit()
        except SQLAlchemyError as e:
            logger.info("failed to commit transaction", exc_info=True)
            raise ServerError() from e
