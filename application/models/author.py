from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base
from .mixins import FirstLastNameValidationMixin

if TYPE_CHECKING:
    from .book import Book


class Author(Base, FirstLastNameValidationMixin):
    name: str
    book_id: Mapped[str | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL")
    )

    books: Mapped[list["Book"]] = relationship(back_populates="authors")

    def __repr__(self):
        return f"""
            Author(
            id={self.id},
            name={self.name}
            book_id={self.book_id}
            )
            """
