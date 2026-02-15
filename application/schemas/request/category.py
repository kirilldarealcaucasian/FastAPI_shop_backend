from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=3)


class UpdateCategoryRequest(BaseModel):
    name: str = Field(min_length=3)
