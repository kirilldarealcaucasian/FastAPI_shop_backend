from typing import TypeAlias, TypeVar
from uuid import UUID

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas import (BookIdS, BookOrderPrimaryIdentifier,
                                 CreateAuthorS,
                                 CreateBookS, CreateCategoryS, CreateImageS,
                                 CreateOrderS, CreatePublisherS,
                                 CreateShoppingSessionS, RegisterUserS,
                                 ReturnBookS, ReturnCategoryS, ReturnImageS,
                                 ReturnOrderS, ReturnPublisherS,
                                 ReturnShoppingSessionS, ReturnUserS,
                                 ShoppingSessionIdS, UpdateAuthorS,
                                 UpdateBookS, UpdateCategoryS, UpdateOrderS,
                                 UpdatePartiallyAuthorS, UpdatePartiallyBookS,
                                 UpdatePartiallyOrderS,
                                 UpdatePartiallyPublisherS,
                                 UpdatePartiallyShoppingSessionS,
                                 UpdatePartiallyUserS, UpdatePublisherS,
                                 UpdateUserS)
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import AlreadyExistsError, DuplicateError, ServerError
from core.exceptions.http_exceptions import EntityDoesNotExist
from core.utils import perform_logging

CreateDataT = TypeVar(
    "CreateDataT",
    CreateBookS,
    CreateOrderS,
    RegisterUserS,
    CreateImageS,
    CreateAuthorS,
    CreatePublisherS,
    CreateCategoryS,
    CreateShoppingSessionS,
)

UpdateDataT = TypeVar(
    "UpdateDataT",
    UpdateBookS,
    UpdateOrderS,
    UpdateUserS,
    UpdateAuthorS,
    UpdateUserS,
    UpdatePublisherS,
    UpdatePartiallyOrderS,
    UpdateCategoryS,
)

PartialUpdateDataT = TypeVar(
    "PartialUpdateDataT",
    UpdatePartiallyBookS,
    UpdatePartiallyUserS,
    UpdatePartiallyAuthorS,
    UpdatePartiallyPublisherS,
    UpdatePartiallyShoppingSessionS,
)

ReturnDataT = TypeVar(
    "ReturnDataT",
    ReturnBookS,
    ReturnOrderS,
    ReturnUserS,
    ReturnImageS,
    ReturnPublisherS,
    ReturnCategoryS,
    ReturnShoppingSessionS,
)

Id: TypeAlias = int | UUID | BookOrderPrimaryIdentifier

CreateReturnDataT = TypeVar("CreateReturnDataT", ShoppingSessionIdS, BookIdS, None)

DomainModelDataT = TypeVar("DomainModelDataT", bound=BaseModel)

# DomainModelDataT = TypeVar(
#     "DomainModelDataT",
#     AuthorS,
#     BookS,
#     BookOrderAssocS,
#     CartItemS,
#     CategoryS,
#     OrderS,
#     PaymentDetailS,
#     PublisherS,
#     ShoppingSessionS,
#     CartItemS,
#     contravariant=True,
# )


class EntityBaseService:
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
        domain_model: DomainModelDataT,
    ) -> Id | CreateReturnDataT:
        try:
            return await repo.create(domain_model=domain_model, session=session)
        except DuplicateError as e:
            raise AlreadyExistsError(e.entity) from e

    @perform_logging
    async def update(
        self,
        repo: OrmEntityRepoInterface,
        session: AsyncSession,
        instance_id: Id,
        domain_model: DomainModelDataT,
    ) -> ReturnDataT | None:
        return await repo.update(
            instance_id=instance_id,
            domain_model=domain_model,
            session=session,
        )

    @perform_logging
    async def get_all(
        self, repo: OrmEntityRepoInterface, session: AsyncSession, **filters
    ) -> list[ReturnDataT]:
        return await repo.get_all(**filters, session=session)

    @perform_logging
    async def get_by_id(
        self,
        session: AsyncSession,
        repo: OrmEntityRepoInterface,
        id: Id,
    ) -> ReturnDataT | None:
        res: ReturnDataT | None = await repo.get_by_id(id=id, session=session)
        if res is None:
            raise EntityDoesNotExist(entity=f"{repo.model}")

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
