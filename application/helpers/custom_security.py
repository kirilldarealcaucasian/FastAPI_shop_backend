
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class CustomSecurity(HTTPBearer):
    """if there is no token in the header in won't raise an exception,
    instead it'll return None"""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        try:
            credentials: HTTPAuthorizationCredentials | None = await super().__call__(
                request
            )
            return credentials
        except HTTPException:
            # logger.debug("failed to retrieve a token from request", exc_info=True)
            return None
