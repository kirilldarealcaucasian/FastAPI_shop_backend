from fastapi import Depends
from pydantic import UUID4
from application.models import Book
from application.services.utils.filters.base_filter import BaseFilter
from application.services.utils.filters.categories_filter import CategoryFilter


class BookFilter(BaseFilter):
    id__eq: UUID4 | None = None
    isbn__eq: str | None = None
    name__eq: str | None = None
    name__ilike: str | None = None
    number_in_stock__eq: int | None = None
    category: CategoryFilter = Depends()
    price_per_unit__gt: float | None = None
    price_per_unit__lt: float | None = None
    price_with_discount__gt: float | None = None
    price_with_discount__lt: float | None = None
    number_in_stock__gte: int | None = None
    number_in_stock__lte: int | None = None

    order_by: str | None = None

    class Meta(BaseFilter.Meta):
        Model = Book