from typing import Union

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.requests import Request
from fastapi.exceptions import HTTPException


class CustomSecurity(HTTPBearer):
    # from logger import logger
    """if there is no token in the header in won't raise an exception,
        instead it'll return None"""
    async def __call__(
            self,
            request: Request
    ) -> Union[HTTPAuthorizationCredentials, None]:
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            return credentials
        except HTTPException:
            # logger.debug("failed to retrieve a token from request", exc_info=True)
            return None