from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseWithoutId
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .book import Book
    from .order import Order


class BookOrderAssoc(BaseWithoutId, TimestampMixin):
    __tablename__ = "book_order_assoc"  # type: ignore

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True
    )
    book_id: Mapped[str] = mapped_column(
        ForeignKey("books.id", ondelete="RESTRICT"), primary_key=True
    )
    count_ordered: Mapped[int] = mapped_column(default=1, server_default="1")

    book: Mapped["Book"] = relationship(back_populates="book_details")
    order: Mapped["Order"] = relationship(back_populates="order_details")

    __table_args__ = (
        UniqueConstraint(
            "order_id", "book_id", name="uq_book_order_assoc_order_id_book_id"
        ),
        PrimaryKeyConstraint("order_id", "book_id", name="pk_book_order_assoc"),
    )

    def __repr__(self):
        return f"""
                BookOrderAssoc(
                order_id={self.order_id},
                book_id={self.book_id},
                count_ordered={self.count_ordered},
                  )
                """
