from functools import wraps
from fastapi import HTTPException, status
from typing import Callable
from core.exceptions import RelatedEntityDoesNotExist, ServerError, EntityDoesNotExist, RepositoryResolutionError, \
    DBError, NotFoundError
from logger import logger


def perform_logging(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        kwargs = dict(kwargs)
        repo = kwargs.get("repo", None)
        domain_model = kwargs.get("domain_model", None)

        if domain_model:
            extra = {"repo": kwargs["repo"], "domain_model": kwargs["domain_model"]}
        else:
            extra = {"repo": str(repo), "domain_model": str(domain_model)}
        try:
            res = await func(*args, **kwargs)
            print("FUNC NAME: ", func.__name__)
            print("RES: ", res)
            if func.__name__ != "delete" and (not res or res is None):
                logger.info("Entity wasn't found", extra=extra)
                raise EntityDoesNotExist()
            return res
        except RepositoryResolutionError as e:
            logger.error("Repository Resolution error", extra=extra, exc_info=True)
            raise ServerError(detail="failed to perform operation due to server error")

        except RelatedEntityDoesNotExist as e:
            logger.debug("Related entity does not exist", exc_info=True, extra=extra)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error in the provided data (cannot find related entity/entities)"
            )
        except DBError as e:
            logger.error(f"Database {func.__name__} error", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong while performing operation"
            )
        except NotFoundError as e:
            logger.debug("Entity wasn't found", exc_info=True)
            raise EntityDoesNotExist()
    return wrapper