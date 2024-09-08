from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from core import OrmEntityRepository
from application.schemas import ReturnUserS, ReturnUserWithOrdersS
from collections import defaultdict
from application.schemas.order_schemas import (
    ReturnOrderIdS,
    AssocBookS,
)
from application.models import User, Order, BookOrderAssoc
from typing import Protocol

from core.base_repos import OrmEntityRepoInterface


class UserInterface(Protocol):
    # async def get_user_with_orders(
    #         self,
    #         session: AsyncSession,
    #         user_id: int
    # ) -> ReturnUserWithOrdersS:
    #     ...

    async def get_user_by_order_id(
            self,
            session: AsyncSession,
            order_id: int
    ) -> ReturnUserS:
        ...


class CombinedUserInterface(
    UserInterface,
    OrmEntityRepoInterface,
    Protocol
):
    pass


class UserRepository(OrmEntityRepository):
    model: User = User

    # async def get_user_with_orders(
    #         self,
    #         session: AsyncSession,
    #         user_id: int
    # ) -> ReturnUserS:
    #     stmt = select(User).where(User.id == user_id) \
    #         .options(selectinload(User.orders)
    #                  .options(selectinload(Order.order_details)
    #                           .options(selectinload(BookOrderAssoc.book))
    #                           ))
    #     user: User = (await session.scalars(stmt)).one_or_none()
    #
    #     if not user:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="User was not found"
    #         )
    #
    #     orders_dict: dict[int, list[AssocBookS]] = defaultdict(list)
    #
    #     for order in user.orders:
    #         for order_detail in order.order_details:
    #             book = AssocBookS(
    #                 name=order_detail.book.name,
    #                 price_per_unit=order_detail.book.price_per_unit,
    #                 number_in_stock=order_detail.book.number_in_stock,
    #                 count_ordered=order_detail.count_ordered)
    #             orders_dict[order.id].append(book)
    #
    #     orders = []
    #     for key, value in orders_dict.items():
    #         orders.append(
    #             ReturnOrderIdS(
    #                 order_id=key,
    #                 books=value
    #             )
    #         )
    #
    #     return ReturnUserS(
    #         orders=orders,
    #         first_name=user.first_name,
    #         last_name=user.last_name,
    #         email=user.email,
    #
    #     )

    async def get_user_by_order_id(
            self,
            session: AsyncSession, order_id: int,
    ) -> ReturnUserS:
        order_stmt = select(Order).where(Order.id == order_id)
        res = await session.execute(order_stmt)
        order: Order = res.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity you're trying to retrieve does not exist"
            )
        user = await self.get_all(session=session, id=order.user_id)
        return user[0]

    async def get_by_id(self, session: AsyncSession, id: int):
        return await super().get_all(session=session, id=id)
