from pydantic import BaseModel


class ImageS(BaseModel):
    book_id: str | None
    url: str | None
