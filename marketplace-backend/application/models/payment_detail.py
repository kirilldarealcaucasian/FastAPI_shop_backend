from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from .base import Base
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .order import Order


class PaymentDetail(Base, TimestampMixin):
    __tablename__ = "payment_details"  # type: ignore

    status: Mapped[str] = mapped_column(server_default="pending", default="pending")
    payment_provider: Mapped[str | None]
    amount: Mapped[float] = mapped_column(default=0.0, server_default="0.0")

    order: Mapped["Order"] = relationship(back_populates="payment_detail")

    def __repr__(self):
        return f"""PaymentDetail(
            id={self.id},
            status={self.status},
            payment_provider={self.payment_provider},
            amount={self.amount}
        )"""
