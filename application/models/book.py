from decimal import Decimal

from sqlalchemy import DECIMAL, CheckConstraint, Computed, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import TimestampMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .category import Category
    from .author import Author
    from .book_order_assoc import BookOrderAssoc
    from .cart_item import CartItem


class Book(Base, TimestampMixin):
    isbn: Mapped[str] = mapped_column(String, primary_key=True, unique=True)
    name: Mapped[str]
    summary: Mapped[str | None]
    language: Mapped[str]
    country: Mapped[str]
    price_per_unit: Mapped[Decimal] = mapped_column(DECIMAL)
    discount: Mapped[Decimal] = mapped_column(DECIMAL(2, 2), server_default=text("0"))
    price_with_discount: Mapped[Decimal] = mapped_column(
        DECIMAL,
        Computed("price_per_unit - (price_per_unit * discount*0.01)"),
    )
    publisher: Mapped[str]
    year_of_publication: Mapped[int]
    number_in_stock: Mapped[int] = mapped_column(server_default=text("0"))
    rating: Mapped[float] = mapped_column(server_default=text("0"))
    image: Mapped[str]

    categories: Mapped[list["Category"]] = relationship(back_populates="books")
    authors: Mapped[list["Author"]] = relationship(back_populates="books")
    book_details: Mapped[list["BookOrderAssoc"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="book")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_cart_items_quantity_positive"),
    )

    def __repr__(self):
        return f"""
        Book(
        id={self.id}
        isbn={self.isbn},
        name={self.name},
        description={self.summary[:30] if self.summary else ""},
        price_per_unit={self.price_per_unit},
        price_with_discount={self.price_with_discount}
        number_in_stock={self.number_in_stock},
        rating={self.rating},
        discount={self.discount},
        created_at={self.created_at},
        updated_at={self.updated_at}
        )"""
