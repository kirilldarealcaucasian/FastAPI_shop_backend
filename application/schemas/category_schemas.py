from pydantic import BaseModel, Field


class ReturnCategoryS(BaseModel):
    name: str = Field(min_length=3)


class CreateCategoryS(BaseModel):
    name: str = Field(min_length=3)


class UpdateCategoryS(BaseModel):
    name: str = Field(min_length=3)


class CategoryId(BaseModel):
    id: int