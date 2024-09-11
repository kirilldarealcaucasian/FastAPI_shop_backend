from fastapi import HTTPException, status


__all__ = (
    "AlreadyExistsError",
    "RelatedEntityDoesNotExist",
    "ServerError",
    "EntityDoesNotExist",
    "UnauthorizedError",
    "RepositoryResolutionError",
    "InvalidModelCredentials",
    "FilterError",
    "BadRequest",
    "OrderingFilterError",
)


class AlreadyExistsError(HTTPException):
    def __init__(self, entity):
        super().__init__(
            detail=f"{entity} already exists",
            status_code=status.HTTP_409_CONFLICT
        )


class RelatedEntityDoesNotExist(HTTPException):
    def __init__(self, entity: str | None = None):
        if entity:
            super().__init__(
                detail=f"{entity} does not exist",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        else:
            super().__init__(
                detail="Invalid ForeignKey reference",
                status_code=status.HTTP_400_BAD_REQUEST)


class InvalidModelCredentials(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            detail=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class EntityDoesNotExist(HTTPException):
    def __init__(self, entity="Entity"):
        super().__init__(
            detail=f"{entity} does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ServerError(HTTPException):
    def __init__(self, detail: str = "Something went wrong"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str | Exception):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class NoCookieError(HTTPException):
    def __init__(self, detail: str = "No cookie required"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

        
class RepositoryResolutionError(ValueError):
    def __init__(self):
        super().__init__("Unable to find desired repo in the repo_collector")


class FilterError(HTTPException):
    def __init__(self):
        super().__init__(
            detail="incorrect filter format / data",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class OrderingFilterError(HTTPException):
    def __init__(self):
        super().__init__(
            detail="incorrect format for order_by filter",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class BadRequest(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class DomainModelConversionError(TypeError):

    def __str__(self):
        return "failed to convert data to domain model"


