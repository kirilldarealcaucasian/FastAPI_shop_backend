from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .book import Book


class Category(Base, TimestampMixin):
    __tablename__ = "categories"  # type: ignore

    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)
    name: Mapped[str] = mapped_column(String, unique=True)

    books: Mapped[list["Book"]] = relationship(
        secondary="book_category_assoc", back_populates="categories"
    )

    def __repr__(self):
        return f"""Category(
            id={self.id},
            name={self.name}
        )"""
