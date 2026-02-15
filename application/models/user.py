from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import Literal

from .base import Base
from .mixins import FirstLastNameValidationMixin, TimestampMixin

Gender = Literal["male", "female"]

if TYPE_CHECKING:
    from .order import Order
    from .shopping_session import ShoppingSession


class User(Base, FirstLastNameValidationMixin, TimestampMixin):
    first_name: Mapped[str]
    last_name: Mapped[str]
    gender: Mapped[Gender] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str]
    role_name: Mapped[str] = mapped_column(default="user", server_default="user")
    date_of_birth: Mapped[date] = mapped_column(Date, server_default=None)

    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
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
