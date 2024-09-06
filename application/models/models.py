from typing import List
from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    Date,
    String,
    Double,
    UUID,
    BIGINT,
    Computed,
    DateTime,
    Index,
    MetaData,
    Table,
    Column,
    Integer
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship, DeclarativeBase, declared_attr,
)
from datetime import date, datetime, timedelta
from typing_extensions import Literal

from application.helpers import generate_uuid
from application.models.mixins import FirstLastNameValidationMixin, TimestampMixin

__all__ = (
    "Base",
    "User",
    "Book",
    "Order",
    "BookOrderAssoc",
    "Author",
    "Publisher",
    "Image",
    "Category",
    "ShoppingSession",
    "CartItem",
    "PaymentDetail",
)

Gender = Literal["male", "female"]

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(naming_convention=convention)

    type_annotation_map = {
        int: BIGINT,
        float: Double
    }

    @declared_attr.directive
    def __tablename__(self):
        return f"{self.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


BookCategoryAssoc = Table(
    "book_category_assoc",
    Base.metadata,
    Column('book_id', UUID, ForeignKey('books.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)  # secondary table


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    __table_args__ = (UniqueConstraint(
        "name", name="uq_categories_name"),
    )
    name: Mapped[str] = mapped_column(unique=True)

    # relationships
    books: Mapped[list["Book"]] = relationship(
        secondary="book_category_assoc",
        back_populates="categories"
    )  # gets books of this category

    def __repr__(self):
        return f"""Category(
            id={self.id},
            name={self.name}
        )"""


class Book(Base, TimestampMixin):
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        default=generate_uuid,
        unique=True
    )
    isbn: Mapped[str] = mapped_column(String, primary_key=True, unique=True)
    name: Mapped[str]
    description: Mapped[str | None]
    price_per_unit: Mapped[float]
    price_with_discount: Mapped[float] = mapped_column(
        Double,
        Computed(
            "price_per_unit - (price_per_unit * (discount*0.01))"),
    )
    number_in_stock: Mapped[int]
    rating: Mapped[float | None]
    discount: Mapped[int | None]

    # relationships
    images: Mapped[list["Image"]] = relationship(back_populates="book")
    book_details: Mapped[list["BookOrderAssoc"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    publishers: Mapped[list["Publisher"]] = relationship(back_populates="books")
    authors: Mapped[list["Author"]] = relationship(back_populates="books")
    cart_items: Mapped[list["CartItem"]] = relationship(back_populates="book")

    #  relationships
    categories: Mapped[list["Category"]] = relationship(
        secondary="book_category_assoc",
        back_populates="books"
    )  # gets categories of this book

    def __repr__(self):
        return f"""
        Book(
        id={self.id}
        isbn={self.isbn},
        name={self.name},
        description={self.description[:30]},
        price_per_unit={self.price_per_unit},
        price_with_discount={self.price_with_discount}
        number_in_stock={self.number_in_stock},
        rating={self.rating},
        discount={self.discount},
        created_at={self.created_at},
        updated_at={self.updated_at}
        )"""


class User(Base, FirstLastNameValidationMixin, TimestampMixin):
    first_name: Mapped[str]
    last_name: Mapped[str]
    gender: Mapped[Gender] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str]
    role_name: Mapped[str | None] = mapped_column(default="user", server_default="user")
    date_of_birth: Mapped[date | None] = mapped_column(Date, server_default=None)

    # relationship
    orders: Mapped[list["Order"] | None] = relationship(back_populates="user",
                                                        cascade="all, delete-orphan")

    shopping_session: Mapped["ShoppingSession"] = relationship(back_populates="user")

    def __repr__(self):
        return f"""
        User(
        id={self.id},
        first_name={self.first_name},
        last_name={self.last_name},
        gender: {self.gender},
        email={self.email},
        hashed_password={self.hashed_password}
        role_name={self.role_name}
        date_of_birth={self.date_of_birth},
        created_at={self.created_at},
        updated_at={self.updated_at}
        )
                """


class PaymentDetail(Base, TimestampMixin):
    __tablename__ = "payment_details"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                     default=generate_uuid,
                                     unique=True
                                     )
    status: Mapped[str] = mapped_column(server_default="pending", default="pending")
    payment_provider: Mapped[str | None]
    amount: Mapped[float] = mapped_column(default=0.0, server_default="0.0")

    # relationships
    order: Mapped["Order"] = relationship(back_populates="payment_detail")

    def __repr__(self):
        return f"""PaymentDetail(
            id={self.id},
            status={self.status},
            payment_provider={self.payment_provider},
            amount={self.amount} 
        )"""


class Order(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    order_status: Mapped[str | None] = mapped_column(default="pending", server_default="pending")
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_sum: Mapped[float] = mapped_column(Double, default=0)
    payment_id: Mapped[str | None] = mapped_column(ForeignKey("payment_details.id", ondelete="RESTRICT"))

    # relationships
    order_details: Mapped[list["BookOrderAssoc"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )

    payment_detail: Mapped[list["PaymentDetail"]] = relationship(
        back_populates="order",
    )

    user: Mapped["User"] = relationship(back_populates="orders")

    def __repr__(self):
        return f"""Order(
        id={self.id}, 
        user_id={self.user_id},
        order_status={self.order_status},
        order_date={self.order_date},
        total_sum={self.total_sum},
        )"""


class BookOrderAssoc(Base):
    __tablename__ = "book_order_assoc"

    __table_args__ = (
        UniqueConstraint("order_id", "book_id", name="uq_book_order_assoc_order_id_book_id"),
    )

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    count_ordered: Mapped[int] = mapped_column(default=1, server_default="1")

    # relationships
    book: Mapped["Book"] = relationship(back_populates="book_details")
    order: Mapped["Order"] = relationship(back_populates="order_details")

    def __repr__(self):
        return f"""
                BookOrderAssoc(
                id={self.id},
                order_id={self.order_id},
                book_id={self.book_id},
                count_ordered={self.count_ordered},
                  )
                """


class Author(Base, FirstLastNameValidationMixin):
    first_name: Mapped[str]
    last_name: Mapped[str]
    book_id: Mapped[str | None] = mapped_column(ForeignKey("books.id", ondelete="SET NULL"))

    # relationships
    books: Mapped[list["Book"]] = relationship(back_populates="authors")

    def __repr__(self):
        return f"""
            Author(
            id={self.id},
            first_name={self.first_name},
            last_name={self.last_name},
            book_id={self.book_id}
            )
            """


class Publisher(Base, FirstLastNameValidationMixin):
    first_name: Mapped[str]
    last_name: Mapped[str]
    book_id: Mapped[str | None] = mapped_column(ForeignKey("books.id", ondelete="SET NULL"))

    # relationships
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


class ShoppingSession(Base, TimestampMixin):
    __tablename__ = "shopping_sessions"

    __table_args__ = (
        Index("ix_shopping_sessions", "expiration_time"),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), default=generate_uuid,
        primary_key=True,
        unique=True
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), unique=True)
    total: Mapped[float | None] = mapped_column(server_default="0", default=0)
    expiration_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now() + timedelta(days=1)
    )

    # relationships
    user: Mapped["User"] = relationship(back_populates="shopping_session")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="shopping_session")

    def __repr__(self):
        return f"""ShoppingSession(
            id={self.id},
            user_id={self.user_id},
            total={self.total},
            expiration_time={self.expiration_time}
        )
            """


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    __table_args__ = (UniqueConstraint(
        "session_id",
        "book_id",
        name="uq_cart_items_session_id_book_id"),
    )

    session_id: Mapped[UUID] = mapped_column(ForeignKey("shopping_sessions.id",
                                                        ondelete="CASCADE",
                                                        ), primary_key=True)
    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id",
                                                     ondelete="RESTRICT",
                                                     ), primary_key=True)
    quantity: Mapped[int]

    __mapper_args__ = {'primary_key': [session_id, book_id]}  # composite primary key

    # relationships
    book: Mapped["Book"] = relationship(back_populates="cart_items")
    shopping_session: Mapped["ShoppingSession"] = relationship(back_populates="cart_items")

    def __repr__(self):
        return f"""CartItem(
            id={self.id},
            book_id={self.book_id},
            quantity={self.quantity},
        )"""


class Image(Base):
    book_id: Mapped[str | None] = mapped_column(ForeignKey("books.id"))
    url: Mapped[str | None]

    book: Mapped["Book"] = relationship(back_populates="images")

    def __repr__(self):
        return f"Image(id={self.id}, book_id={self.book_id}, url={self.url})"
