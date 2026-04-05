from functools import wraps
from typing import Callable

from fastapi import HTTPException, status
from loguru import logger

from shared_lib.exceptions import (
    DBError,
    EntityDoesNotExist,
    NotFoundError,
    RelatedEntityDoesNotExist,
)
from typing import TypeVar, ParamSpec, Awaitable

P = ParamSpec("P")
R = TypeVar("R")


def perform_logging(
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Applies logging scenarios for a function"""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        repo = kwargs.get("repo", None)
        domain_model = kwargs.get("domain_model", None)

        if domain_model:
            extra = {"repo": kwargs["repo"], "domain_model": kwargs["domain_model"]}
        else:
            extra = {"repo": str(repo), "domain_model": str(domain_model)}
        try:
            res = await func(*args, **kwargs)
            if func.__name__ != "delete" and (not res or res is None):
                logger.info("Entity wasn't found", extra=extra)
                raise EntityDoesNotExist()
            return res
        except RelatedEntityDoesNotExist as e:
            logger.debug("Related entity does not exist", exc_info=True, extra=extra)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error in the provided data (cannot find related entity/entities)",
            ) from e
        except DBError as e:
            logger.error(f"Database {func.__name__} error", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong",
            ) from e
        except NotFoundError as e:
            logger.debug(f"{e.entity} wasn't found", exc_info=True)
            raise EntityDoesNotExist(entity=e.entity) from e

    return wrapper
