from datetime import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:  # pylint: disable=all
        return mapped_column(TIMESTAMP(timezone=True), default=datetime.now)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:  # pytlint: disable=all
        return mapped_column(TIMESTAMP(timezone=True), default=datetime.now)
