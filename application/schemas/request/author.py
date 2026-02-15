from pydantic import BaseModel


class CreateAuthorRequest(BaseModel):
    id: int
    first_name: str
    last_name: str


class UpdateAuthorRequest(BaseModel):
    first_name: str
    last_name: str


class UpdatePartiallyAuthorRequest(BaseModel):
    first_name: str | None
    last_name: str | None
