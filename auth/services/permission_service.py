from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.exceptions import UnauthorizedError
from auth.helpers import get_token_payload


class PermissionService:
    @staticmethod
    def get_admin_permission(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> bool:
        payload = get_token_payload(credentials=credentials)

        if payload.get("role") != "admin":
            raise UnauthorizedError(
                detail="You don't have permission to perform this action"
            )

        return True
