from pydantic import Field

from ....models import Category
from .base_filter import BaseFilter


class CategoryFilter(BaseFilter):
    name__eq: str | None = Field(default=None, alias="category_name__eq")

    order_by: str | None = None

    class Meta(BaseFilter.Meta):
        Model = Category
