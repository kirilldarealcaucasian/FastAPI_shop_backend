from typing import Annotated
from fastapi import Depends
from ..services import UserService
from ..repositories.user_repo import UserRepository, CombinedUserInterface
from ..repositories.order_repo import OrderRepository, CombinedOrderRepositoryInterface


def get_user_service(
    user_repo: Annotated[CombinedUserInterface, Depends(UserRepository)],
    order_repo: Annotated[CombinedOrderRepositoryInterface, Depends(OrderRepository)],
) -> UserService:
    return UserService(user_repo=user_repo, order_repo=order_repo)
