from pydantic import BaseModel


class CategoryS(BaseModel):
    id: int | None
    name: str
