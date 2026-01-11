from pydantic import BaseModel


class PublisherS(BaseModel):
    first_name: str | None
    last_name: str | None
    book_id: str | None
