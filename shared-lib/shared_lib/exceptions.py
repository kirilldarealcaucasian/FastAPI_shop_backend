from fastapi import HTTPException, status


class AlreadyExistsError(HTTPException):
    def __init__(self, entity: str):
        super().__init__(
            detail=f"{entity} already exists",
            status_code=status.HTTP_409_CONFLICT,
        )


class ConflictErrorHTTP(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Failed to perform operation due to conflict",
            status_code=status.HTTP_409_CONFLICT,
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
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class InvalidModelCredentials(HTTPException):
    def __init__(self, message: str):
        super().__init__(
            detail=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class EntityDoesNotExist(HTTPException):
    def __init__(self, entity: str = "Entity"):
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


class ForbiddenError(HTTPException):
    def __init__(self):
        super().__init__(
            detail="forbidden",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NoCookieError(HTTPException):
    def __init__(self, detail: str = "No cookie required"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class FilterError(HTTPException):
    def __init__(self):
        super().__init__(
            detail="incorrect filter format / data",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class OrderingFilterError(HTTPException):
    def __init__(self):
        super().__init__(
            detail="incorrect format for order_by filter",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class BadRequest(HTTPException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class DomainModelConversionError(TypeError):
    def __str__(self) -> str:
        return "failed to convert data to domain model"


class DuplicateError(Exception):
    def __init__(self, entity: str, traceback: str | None = None):
        self.entity = entity
        self.traceback = traceback

    def __str__(self) -> str:
        if self.traceback:
            return f"{self.entity} already exists, {self.traceback}"
        return f"{self.entity} already exists"


class DBError(Exception):
    def __init__(self, traceback: str = ""):
        self.traceback = traceback

    def __str__(self) -> str:
        return f"Traceback: {self.traceback}"


class NotFoundError(Exception):
    def __init__(self, entity: str = "Entity"):
        self.entity = entity

    def __str__(self) -> str:
        return f"{self.entity} wasn't found"


class ConflictError(Exception):
    def __init__(self, entity: str, traceback: str | None = None):
        self.entity = entity
        self.traceback = traceback

    def __str__(self) -> str:
        return f"{self.entity} conflict: {self.traceback}"


class DeletionError(Exception):
    def __init__(self, entity: str):
        self.entity = entity

    def __str__(self) -> str:
        return f"Failed to delete {self.entity}"


class RemoteBucketDeletionError(Exception):
    def __str__(self) -> str:
        return "Failed to delete image from the remote bucket"


__all__ = (
    "AlreadyExistsError",
    "BadRequest",
    "ConflictError",
    "ConflictErrorHTTP",
    "DBError",
    "DeletionError",
    "DomainModelConversionError",
    "DuplicateError",
    "EntityDoesNotExist",
    "FilterError",
    "ForbiddenError",
    "InvalidModelCredentials",
    "NoCookieError",
    "NotFoundError",
    "OrderingFilterError",
    "RelatedEntityDoesNotExist",
    "RemoteBucketDeletionError",
    "ServerError",
    "UnauthorizedError",
)
