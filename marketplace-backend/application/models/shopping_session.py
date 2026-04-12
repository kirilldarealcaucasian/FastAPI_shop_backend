from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseWithoutId
from .mixins import TimestampMixin

if TYPE_CHECKING:
    from .cart_item import CartItem


class ShoppingSession(BaseWithoutId, TimestampMixin):
    __tablename__ = "shopping_sessions"  # type: ignore

    __table_args__ = (Index("ix_shopping_sessions", "expiration_time"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(unique=True)
    total: Mapped[Decimal] = mapped_column(server_default="0", default=0)
    expiration_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now() + timedelta(days=1)
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="shopping_session"
    )

    def __repr__(self):
        return f"""ShoppingSession(
            id={self.id},
            user_id={self.user_id},
            total={self.total},
            expiration_time={self.expiration_time}
        )
            """
