from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic

from core.base_repos import OrmEntityRepoInterface
from core.exceptions import RepositoryResolutionError, \
    DuplicateError, AlreadyExistsError, ServerError
from application.schemas import (
    CreateBookS,
    CreateOrderS,
    CreateImageS,
    CreateAuthorS,
    CreatePublisherS,
    RegisterUserS,
    UpdateBookS,
    UpdateOrderS,
    UpdateAuthorS,
    UpdateUserS,
    UpdateCategoryS,
    UpdatePublisherS,
    UpdatePartiallyBookS,
    UpdatePartiallyUserS,
    UpdatePartiallyAuthorS,
    UpdatePartiallyPublisherS,
    ReturnBookS,
    ReturnOrderS,
    ReturnUserS,
    ReturnImageS,
    ReturnPublisherS, UpdatePartiallyOrderS,
    CreateCategoryS, ReturnCategoryS,
    ReturnShoppingSessionS, ShoppingSessionIdS,
    CreateShoppingSessionS,
    UpdatePartiallyShoppingSessionS, BookIdS, CartPrimaryIdentifier, BookOrderPrimaryIdentifier
)
from application.schemas.domain_model_schemas import \
    (
    AuthorS,
    BookS,
    BookOrderAssocS,
    CartItemS,
    CategoryS,
    OrderS,
    PaymentDetailS,
    PublisherS,
    ShoppingSessionS,
    ImageS, UserS
)
from logger import logger
from core.utils import perform_logging
# from core.base_repos import OrmEntityRepoInterface

CreateDataT = TypeVar(
    "CreateDataT",
    CreateBookS, CreateOrderS, RegisterUserS,
    CreateImageS, CreateAuthorS, CreatePublisherS,
    CreateCategoryS, CreateShoppingSessionS
)

UpdateDataT = TypeVar(
    "UpdateDataT",
    UpdateBookS, UpdateOrderS, UpdateUserS,
    UpdateAuthorS, UpdateUserS, UpdatePublisherS,
    UpdatePartiallyOrderS, UpdateCategoryS
)

PartialUpdateDataT = TypeVar(
    "PartialUpdateDataT",
    UpdatePartiallyBookS, UpdatePartiallyUserS,
    UpdatePartiallyAuthorS, UpdatePartiallyPublisherS,
    UpdatePartiallyShoppingSessionS
)

ReturnDataT = TypeVar(
    "ReturnDataT", ReturnBookS, ReturnOrderS,
    ReturnUserS, ReturnImageS, ReturnPublisherS,
    ReturnCategoryS, ReturnShoppingSessionS
)

CreateReturnDataT = TypeVar("CreateReturnDataT", ShoppingSessionIdS, BookIdS, None)

ArgDataT = TypeVar("ArgDataT", str, int, UUID)

DomainModelDataT = TypeVar(
    "DomainModelDataT",
    UserS, AuthorS, BookS,
    BookOrderAssocS, CartItemS, CategoryS,
    OrderS, PaymentDetailS, PublisherS,
    ShoppingSessionS, ImageS
)

MergedDataT = TypeVar("MergedDataT", )

IdentityDataT = TypeVar("IdentityDataT", str, int, UUID, CartPrimaryIdentifier, BookOrderPrimaryIdentifier)

RepoInterface = TypeVar("RepoInterface")


class RepositoryResolver:
    """
    returns desired repository from the EntityBaseService attributes
    (EntityBaseService might be initialized by different repositories
    from service layer)
    """

    def __init__(self, repository_pool: dict):
        self.repo_pool: dict = repository_pool

    def __call__(
            self,
            desired_repo: OrmEntityRepoInterface,
    ) -> RepoInterface:
        for repo in self.repo_pool.values():
            if repo == desired_repo:
                return repo
        raise RepositoryResolutionError


class EntityBaseService(
    Generic[
        DomainModelDataT, CreateDataT,
        UpdateDataT, PartialUpdateDataT,
        ReturnDataT, CreateReturnDataT,
        ArgDataT,
    ]
):
    """
    Takes out responsibility of handling exceptions in each of the service classes.
    EntityBaseService calls to the repository defined in each subclass of EntityBaseService
    """

    def __init__(self, **repos):
        for repo_name, instance in repos.items():
            # store received repository instances in the attributes
            setattr(self, repo_name, instance)
        self.repository_resolver = RepositoryResolver(repository_pool=vars(self))

    @perform_logging
    async def create(
            self,
            repo: RepoInterface,
            session: AsyncSession,
            domain_model: DomainModelDataT
    ) -> CreateReturnDataT:
        extra = {"repo": repo, "domain_model": domain_model}
        try:
            id = await self.repository_resolver(repo).create(
                domain_model=domain_model,
                session=session
            )
            return id
        except DuplicateError as e:
            logger.debug(f"{e.entity} Already exists", exc_info=True, extra=extra)
            raise AlreadyExistsError(e.entity)

    @perform_logging
    async def update(
            self,
            repo: RepoInterface,
            session: AsyncSession,
            instance_id: ArgDataT,
            domain_model: DomainModelDataT
    ) -> ReturnDataT:
        return await self.repository_resolver(repo).update(
            instance_id=instance_id,
            domain_model=domain_model,
            session=session,
        )

    @perform_logging
    async def get_all(
            self,
            repo: RepoInterface,
            session: AsyncSession,
            **filters
    ) -> list[ReturnDataT] | ReturnDataT:
        return await self.repository_resolver(repo).get_all(
            **filters,
            session=session
        )

    @perform_logging
    async def get_by_id(
            self,
            session: AsyncSession,
            repo: RepoInterface,
            id: IdentityDataT,
    ) -> ReturnDataT:
        return await self.repository_resolver(repo).get_by_id(id=id, session=session)

    @perform_logging
    async def delete(
            self,
            repo: RepoInterface,
            session: AsyncSession,
            instance_id: ArgDataT,

    ) -> None:
        _ = await self.repository_resolver(repo).delete(instance_id=instance_id, session=session)

    async def commit(self, session: AsyncSession):
        try:
            await session.commit()
        except SQLAlchemyError:
            logger.info("failed to commit transaction", exc_info=True)
            raise ServerError()
