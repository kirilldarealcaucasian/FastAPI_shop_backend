from typing import Annotated
from fastapi import Depends
from ..repositories.order_repo import OrderRepository, CombinedOrderRepositoryInterface
from ..services.user_service import UserService


def get_user_service(
    order_repo: Annotated[CombinedOrderRepositoryInterface, Depends(OrderRepository)],
) -> UserService:
    return UserService(order_repo=order_repo)
