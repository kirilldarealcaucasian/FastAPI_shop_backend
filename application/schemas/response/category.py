from pydantic import BaseModel, Field


class GetCategoryResponse(BaseModel):
    name: str = Field(min_length=3)


class CategoryIdResponse(BaseModel):
    id: int
