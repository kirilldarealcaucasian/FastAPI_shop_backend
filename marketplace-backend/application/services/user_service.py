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

    @staticmethod
    def _split_name(name: str) -> tuple[str, str]:
        parts = name.split(" ", maxsplit=1)
        first_name = parts[0] if parts else ""
        last_name = parts[1] if len(parts) > 1 else first_name
        return first_name, last_name

    async def get_all_users(
        self, session: AsyncSession, pagination: PaginationS
    ) -> Sequence[GetUserResponse] | GetUserResponse:
        try:
            users = await super(UserService, self).get_all(
                repo=self.user_repo,
                session=session,
                page=pagination.page,
                limit=pagination.limit,
            )
        except NotFoundError:
            raise EntityDoesNotExist(entity="User")
        return users

    async def get_user_by_id(self, session: AsyncSession, id: Id) -> GetUserResponse:
        user: User = await super(UserService, self).get_by_id(
            repo=self.user_repo, session=session, id=id
        )  # if not exits http exception will be raised
        first_name, last_name = self._split_name(user.name)

        return GetUserResponse(
            id=user.id,
            first_name=first_name,
            last_name=last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.role_name,
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
            first_name, last_name = self._split_name(user.first_name)
            return GetUserWithOrdersResponse(
                first_name=first_name,
                last_name=last_name,
                email=user.email,
                orders=[],
            )

        return_orders: list[GetOrderResponse] = []

        for order in user.orders:
            order_books = order_assembler(order_details=order.order_details)
            return_orders.append(GetOrderResponse(order_id=order.id, books=order_books))

        first_name, last_name = self._split_name(user.name)
        return GetUserWithOrdersResponse(
            first_name=first_name,
            last_name=last_name,
            email=user.email,
            orders=return_orders,
        )

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> GetUserResponse:
        _ = await super(UserService, self).get_by_id(
            session=session, repo=self.order_repo, id=order_id
        )  # if no order, http_exception will be raised

        user = await self.user_repo.get_user_by_order_id(
            session=session, order_id=order_id
        )
        first_name, last_name = self._split_name(user.name)

        return GetUserResponse(
            id=user.id,
            first_name=first_name,
            last_name=last_name,
            email=user.email,
            gender=user.gender,
            role_name=user.role_name,
        )

    async def delete_user(self, session: AsyncSession, user_id: str | int) -> None:
        await super(UserService, self).delete(
            repo=self.user_repo, session=session, instance_id=user_id
        )
        await super(UserService, self).commit(session=session)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str | int,
        dto: UpdateUserRequest | UpdatePartiallyUserRequest,
    ) -> None:
        data: dict = dto.model_dump(exclude_unset=True, exclude_none=True)
        if not dto:
            raise InvalidModelCredentials(message="invalid data")

        return await super(UserService, self).update(
            session=session,
            repo=self.user_repo,
            instance_id=user_id,
            orm_model=data,
        )
