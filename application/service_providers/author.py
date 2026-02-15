from typing import Annotated
from fastapi import Depends
from ..services.author_service import AuthorService
from ..repositories.orm_entity_repo import OrmEntityRepoInterface
from ..repositories.author_repo import AuthorRepository


def get_author_service(
    author_repo: Annotated[OrmEntityRepoInterface, Depends(AuthorRepository)],
) -> AuthorService:
    return AuthorService(author_repo=author_repo)
