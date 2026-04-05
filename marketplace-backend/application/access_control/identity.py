from dataclasses import dataclass

from fastapi import Header

from shared_lib.exceptions import UnauthorizedError


@dataclass(frozen=True)
class RequestIdentity:
    user_id: int
    role: str


def get_request_identity(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> RequestIdentity:
    if x_user_id is None or not x_user_role:
        raise UnauthorizedError(detail="Missing identity headers")
    return RequestIdentity(user_id=x_user_id, role=x_user_role)


def get_optional_user_id(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> int | None:
    return x_user_id
