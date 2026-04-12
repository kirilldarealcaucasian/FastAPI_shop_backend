from collections.abc import Sequence
from dataclasses import dataclass

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.order_repo import CombinedOrderRepositoryInterface
from ..schemas.filters import PaginationS
from ..schemas.request.user import UpdatePartiallyUserRequest, UpdateUserRequest
from ..schemas.response.order import GetOrderResponse
from ..schemas.response.user import GetUserResponse, GetUserWithOrdersResponse
from ..services.order_service.utils import order_assembler
from ..settings import settings
from shared_lib.exceptions import DBError, EntityDoesNotExist, NotFoundError, ServerError


@dataclass(slots=True, frozen=True)
class UserService:
    order_repo: CombinedOrderRepositoryInterface

    async def get_all_users(
        self, session: AsyncSession, pagination: PaginationS
    ) -> Sequence[GetUserResponse] | GetUserResponse:
        users = await self._request_json(
            method="GET",
            path="/users",
            params={"page": pagination.page, "limit": pagination.limit},
        )
        return [GetUserResponse.model_validate(user) for user in users]

    async def get_user_by_id(self, session: AsyncSession, id: int) -> GetUserResponse:  # noqa
        user = await self._request_json(method="GET", path=f"/users/{id}")
        return GetUserResponse.model_validate(user)

    async def get_user_with_orders(
        self, session: AsyncSession, user_id: int
    ) -> GetUserWithOrdersResponse:
        user = await self.get_user_by_id(session=session, id=user_id)

        try:
            order_details = await self.order_repo.get_orders_by_user_id(
                session=session, user_id=user_id
            )
        except NotFoundError:
            return GetUserWithOrdersResponse(
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                orders=[],
            )
        except DBError:
            raise ServerError()

        orders_by_id: dict[int, list] = {}
        for detail in order_details:
            orders_by_id.setdefault(detail.order_id, []).append(detail)

        orders: list[GetOrderResponse] = []
        for order_id, details in orders_by_id.items():
            books = order_assembler(order_details=details)
            orders.append(GetOrderResponse(order_id=order_id, books=books))

        return GetUserWithOrdersResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            orders=orders,
        )

    async def get_user_by_order_id(
        self,
        session: AsyncSession,
        order_id: int,
    ) -> GetUserResponse:
        orders = await self.order_repo.get_all(session=session, id=order_id, limit=1)
        if not orders:
            raise EntityDoesNotExist(entity="Order")

        order = orders[0]
        return await self.get_user_by_id(session=session, id=order.user_id)

    async def delete_user(self, session: AsyncSession, user_id: str | int) -> None:
        await self._request_json(method="DELETE", path=f"/users/{int(user_id)}")

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str | int,
        dto: UpdateUserRequest | UpdatePartiallyUserRequest,
    ) -> None:
        method = "PUT" if isinstance(dto, UpdateUserRequest) else "PATCH"
        payload = dto.model_dump(exclude_unset=True, exclude_none=True)
        await self._request_json(
            method=method,
            path=f"/users/{int(user_id)}",
            data=payload,
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: dict | None = None,
    ) -> dict | list | None:
        timeout = aiohttp.ClientTimeout(total=settings.AUTH_SERVICE_TIMEOUT_SECONDS)
        url = f"{settings.AUTH_SERVICE_BASE_URL}{path}"

        try:
            async with aiohttp.ClientSession(timeout=timeout) as http:
                async with http.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                ) as response:
                    if response.status == 404:
                        if "users" in path:
                            raise EntityDoesNotExist(entity="User")
                        raise EntityDoesNotExist(entity="Entity")

                    if response.status >= 400:
                        raise ServerError("auth service request failed")

                    if response.status == 204:
                        return None

                    return await response.json()
        except aiohttp.ClientError as exc:
            raise ServerError("auth service is unavailable") from exc
