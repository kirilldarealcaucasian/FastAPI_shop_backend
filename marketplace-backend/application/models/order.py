from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .mixins import TimestampMixin
from .base import Base
from .order_status import OrderStatus


if TYPE_CHECKING:
    from .associations import BookOrderAssoc
    from .payment_detail import PaymentDetail
    from .user import User


class Order(Base, TimestampMixin):
    user_id: Mapped[int] = mapped_column()
    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status_enum",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_sum: Mapped[Decimal] = mapped_column(Numeric, default=0)
    payment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_details.id", ondelete="RESTRICT")
    )

    order_details: Mapped[list["BookOrderAssoc"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payment_detail: Mapped[list["PaymentDetail"]] = relationship(
        back_populates="order",
    )
    user: Mapped["User"] = relationship(
        back_populates="orders",
        primaryjoin="Order.user_id == User.id",
        foreign_keys="Order.user_id",
    )

    def __repr__(self):
        return f"""Order(
        id={self.id},
        user_id={self.user_id},
        order_status={self.order_status},
        order_date={self.order_date},
        total_sum={self.total_sum},
        )"""
