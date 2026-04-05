from sqlalchemy.orm import Mapped, relationship
from typing import TYPE_CHECKING

from .associations import BookAuthorsAssoc
from .base import Base

if TYPE_CHECKING:
    from .book import Book


class Author(Base):
    name: Mapped[str]
    books: Mapped[list["Book"]] = relationship(
        secondary=BookAuthorsAssoc, back_populates="authors"
    )

    def __repr__(self):
        return f"""
            Author(
            id={self.id},
            name={self.name}
            )
            """
