from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.response.user import GetUserWithOrdersResponse, GetUserResponse
from ..schemas.request.user import UpdatePartiallyUserRequest, UpdateUserRequest
from ..types import Id

from ..models import User
from ..repositories.order_repo import (
    CombinedOrderRepositoryInterface,
)
from ..repositories.user_repo import CombinedUserInterface

from ..schemas.filters import PaginationS
from ..schemas.response.order import GetOrderResponse
from ..services.order_service.utils import order_assembler
from .entity_base_service import EntityBaseService
from shared_lib.exceptions import (
    EntityDoesNotExist,
    InvalidModelCredentials,
    NotFoundError,
)
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class UserService(EntityBaseService):
    user_repo: CombinedUserInterface
    order_repo: CombinedOrderRepositoryInterface

    async def get_all_users(
        self, session: AsyncSession, pagination: PaginationS
    ) -> Sequence[GetUserResponse] | GetUserResponse:
        try:
            users = await super().get_all(
                repo=self.user_repo,
                session=session,
                page=pagination.page,
                limit=pagination.limit,
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="User")
        return users

    async def get_user_by_id(self, session: AsyncSession, id: Id) -> GetUserResponse:
        user: User = await super().get_by_id(
            repo=self.user_repo, session=session, id=id
        )  # if not exits http exception will be raised

        return GetUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.gender,
        )

    async def get_user_with_orders(
        self, session: AsyncSession, user_id: int
    ) -> GetUserWithOrdersResponse:
        user = await self.get_user_by_id(
            session=session, id=user_id
        )  # if no user, http_exception will be raised

        try:
            user = await self.user_repo.get_user_with_orders(
                session=session, user_id=user_id
            )
        except NotFoundError:
            return GetUserWithOrdersResponse(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                orders=[],
            )

        return_orders: list[GetOrderResponse] = []

        for order in user.orders:
            order_books = order_assembler(order_details=order.order_details)
            return_orders.append(GetOrderResponse(order_id=order.id, books=order_books))

        return GetUserWithOrdersResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            orders=return_orders,
        )

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> GetUserResponse:
        _ = await super().get_by_id(
            session=session, repo=self.order_repo, id=order_id
        )  # if no order, http_exception will be raised

        user = await self.user_repo.get_user_by_order_id(
            session=session, order_id=order_id
        )

        return GetUserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.role_name,
        )

    async def delete_user(self, session: AsyncSession, user_id: str | int) -> None:
        await super().delete(repo=self.user_repo, session=session, instance_id=user_id)
        await super().commit(session=session)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str | int,
        dto: UpdateUserRequest | UpdatePartiallyUserRequest,
    ) -> None:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        if not dto:
            raise InvalidModelCredentials(message="invalid data")

        return await super().update(
            session=session,
            repo=self.user_repo,
            instance_id=user_id,
            orm_model=data,
        )
