from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .book_order_assoc import BookOrderAssoc
    from .payment_detail import PaymentDetail
    from .user import User


class Order(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    order_status: Mapped[str | None] = mapped_column(
        default="pending", server_default="pending"
    )
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_sum: Mapped[float] = mapped_column(Double, default=0)
    payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_details.id", ondelete="RESTRICT")
    )

    order_details: Mapped[list["BookOrderAssoc"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
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
