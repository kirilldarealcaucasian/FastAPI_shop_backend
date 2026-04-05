from pydantic import BaseModel


class CreatePublisherRequest(BaseModel):
    id: int
    first_name: str
    last_name: str


class UpdatePublisherRequest(BaseModel):
    first_name: str
    last_name: str


class UpdatePartiallyPublisherRequest(BaseModel):
    first_name: str | None
    last_name: str | None
