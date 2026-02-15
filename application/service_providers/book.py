from typing import Annotated
from fastapi import Depends
from ..services import BookService
from ..repositories.book_repo import BookRepository, CombinedBookRepoInterface


def get_book_service(
    book_repo: Annotated[CombinedBookRepoInterface, Depends(BookRepository)],
) -> BookService:
    return BookService(book_repo=book_repo)
