from fastapi import Depends
from typing import Annotated
from ..services.shopping_session_service import ShoppingSessionService
from ..repositories.shopping_session_repo import (
    CombinedShoppingSessionRepositoryInterface,
    ShoppingSessionRepository,
)


def get_shopping_session_service(
    repo: Annotated[
        CombinedShoppingSessionRepositoryInterface, Depends(ShoppingSessionRepository)
    ],
) -> ShoppingSessionService:
    return ShoppingSessionService(shopping_session_repo=repo)
