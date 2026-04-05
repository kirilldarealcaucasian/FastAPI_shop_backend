from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .associations import BookCategoryAssoc
from .base import Base

if TYPE_CHECKING:
    from .book import Book


class Category(Base):
    __tablename__ = "categories"  # type: ignore
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    name: Mapped[str] = mapped_column(String, unique=True)

    books: Mapped[list["Book"]] = relationship(
        secondary=BookCategoryAssoc, back_populates="categories"
    )

    def __repr__(self):
        return f"""Category(
            id={self.id},
            name={self.name}
        )"""
