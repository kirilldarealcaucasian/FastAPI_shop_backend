from typing import Annotated
from fastapi import Depends
from ..services import CategoryService
from ..repositories.book_repo import BookRepository, CombinedBookRepoInterface


def get_category_service(
    category_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
) -> CategoryService:
    return CategoryService(category_repo=category_repo)
