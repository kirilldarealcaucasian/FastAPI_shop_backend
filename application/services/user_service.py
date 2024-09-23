from typing import Annotated, Union

from fastapi import Depends
from pydantic import ValidationError, PydanticSchemaGenerationError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models import Order, BookOrderAssoc, User
from application.repositories.order_repo import (
    CombinedOrderRepositoryInterface,
    OrderRepository
)
from application.repositories.user_repo import CombinedUserInterface
from application.schemas.domain_model_schemas import UserS
from application.repositories.user_repo import UserRepository
from application.schemas import (
    ReturnUserS,
    UpdateUserS,
    UpdatePartiallyUserS,
    ReturnUserWithOrdersS, ReturnOrderS,
)
from application.schemas.filters import PaginationS
from application.schemas.order_schemas import AssocBookS
from application.services.order_service.utils import order_assembler
from core.exceptions import EntityDoesNotExist, NotFoundError, ServerError, \
    InvalidModelCredentials
from logger import logger
from core.entity_base_service import EntityBaseService


class UserService(EntityBaseService):
    def __init__(
        self,
        user_repo: Annotated[CombinedUserInterface, Depends(UserRepository)],
        order_repo: Annotated[CombinedOrderRepositoryInterface, Depends(OrderRepository)]
    ):
        super().__init__(
            user_repo=user_repo,
            order_repo=order_repo
        )
        self._user_repo: CombinedUserInterface = user_repo
        self._order_repo: CombinedOrderRepositoryInterface = order_repo

    async def get_all_users(
        self, session: AsyncSession, pagination: PaginationS
    ) -> list[ReturnUserS] | ReturnUserS:
        try:
            users = await super().get_all(
                repo=self._user_repo,
                session=session,
                page=pagination.page,
                limit=pagination.limit,
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="User")
        return users

    async def get_user_by_id(
        self,
        session: AsyncSession,
        id: int
    ) -> ReturnUserS:
        user: User = await super().get_by_id(
            repo=self._user_repo,
            session=session,
            id=id
        )  # if not exits http exception will be raised

        return ReturnUserS(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.gender,
        )

    async def get_user_with_orders(
        self, session: AsyncSession, user_id: int
    ) -> ReturnUserWithOrdersS:
        user: ReturnUserS = await self.get_user_by_id(
            session=session,
            id=user_id
        )  # if no user, http_exception will be raised

        try:
            user: Union[User, None] = await self._user_repo.get_user_with_orders(
                session=session, user_id=user_id
            )
        except NotFoundError as e:
            return ReturnUserWithOrdersS(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                orders=[]
            )

        orders: list[Order] = user.orders
        return_orders: list[ReturnOrderS] = []

        for order in orders:
            order_details: list[BookOrderAssoc] = order.order_details

            order_books: list[AssocBookS] = order_assembler(order_details=order_details)
            return_orders.append(
                ReturnOrderS(
                    order_id=order.id,
                    books=order_books
                )
            )

        return ReturnUserWithOrdersS(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            orders=return_orders
        )

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> ReturnUserS:

        _ = await super().get_by_id(
            session=session,
            repo=self._order_repo,
            id=order_id
        )  # if no order, http_exception will be raised

        user = await self._user_repo.get_user_by_order_id(
            session=session,
            order_id=order_id
        )

        return ReturnUserS(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.role_name,
        )

    async def delete_user(
        self, session: AsyncSession, user_id: str | int
    ) -> None:
        await super().delete(
            repo=self._user_repo, session=session, instance_id=user_id
        )
        await super().commit(session=session)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str | int,
        dto: UpdateUserS | UpdatePartiallyUserS,
    ) -> None:
        dto: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        if not dto:
            raise InvalidModelCredentials(message="invalid data")

        try:
            domain_model = UserS(**dto)
        except (ValidationError, PydanticSchemaGenerationError):
            logger.error(
                "Failed to generate domain model",
                extra={"dto": dto},
                exc_info=True
            )
            raise ServerError()

        return await super().update(
            session=session,
            repo=self._user_repo,
            instance_id=user_id,
            domain_model=domain_model
        )
