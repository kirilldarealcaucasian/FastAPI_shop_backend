from pydantic import BaseModel


class CreatePublisherS(BaseModel):
    id: int
    first_name: str
    last_name: str


class ReturnPublisherS(BaseModel):
    first_name: str
    last_name: str


class UpdatePublisherS(BaseModel):
    first_name: str
    last_name: str


class UpdatePartiallyPublisherS(BaseModel):
    first_name: str | None
    last_name: str | None


class PublisherId(BaseModel):
    id: int
