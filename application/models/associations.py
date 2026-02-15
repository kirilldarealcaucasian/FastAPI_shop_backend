from sqlalchemy import UUID as sqlalc_UUID, Column, ForeignKey, Integer, Table

from .base import Base

BookCategoryAssoc = Table(
    "book_category_assoc",
    Base.metadata,
    Column("book_id", sqlalc_UUID, ForeignKey("books.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id"), primary_key=True),
)
