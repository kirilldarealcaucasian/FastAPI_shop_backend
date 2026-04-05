from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseWithoutId
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .book import Book
    from .shopping_session import ShoppingSession


class CartItem(BaseWithoutId, TimestampMixin):
    __tablename__ = "cart_items"  # type: ignore

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "shopping_sessions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey(
            "books.id",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(default=1, server_default="1")

    book: Mapped["Book"] = relationship(back_populates="cart_items")
    shopping_session: Mapped["ShoppingSession"] = relationship(
        back_populates="cart_items"
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id", "book_id", name="uq_cart_items_session_id_book_id"
        ),
        PrimaryKeyConstraint("session_id", "book_id", name="pk_cart_items"),
    )

    def __repr__(self):
        return f"""CartItem(
            "sessiob_id={self.session_id}
            book_id={self.book_id},
            quantity={self.quantity},
        )"""
