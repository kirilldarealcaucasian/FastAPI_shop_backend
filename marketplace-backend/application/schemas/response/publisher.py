from pydantic import BaseModel


class GetPublisherResponse(BaseModel):
    first_name: str
    last_name: str


class PublisherIdResponse(BaseModel):
    id: int
