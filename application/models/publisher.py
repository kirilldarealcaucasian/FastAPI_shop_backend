from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base
from .mixins import FirstLastNameValidationMixin

if TYPE_CHECKING:
    from .book import Book


class Publisher(Base, FirstLastNameValidationMixin):
    first_name: Mapped[str]
    last_name: Mapped[str]
    book_id: Mapped[str | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL")
    )

    books: Mapped[list["Book"]] = relationship(back_populates="publishers")

    def __repr__(self):
        return f"""
            Publisher(
            id={self.id},
            first_name={self.first_name},
            last_name={self.last_name},
            book_id={self.book_id}
            )
            """
