from datetime import datetime

from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, validates

__all__ = ("FirstLastNameValidationMixin", "TimestampMixin")


class FirstLastNameValidationMixin:

    @validates("first_name")
    def validate_first_name(self, key: str, name: str) -> str:
        if len(name) < 2:
            raise ValueError("First name should be at least 2 characters")
        return name

    @validates("last_name")
    def validate_last_name(self, key: str, last_name: str) -> str:
        if len(last_name) < 2:
            raise ValueError("Last name should be at least 2 characters")
        return last_name


class TimestampMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:  # pylint: disable=all
        return mapped_column(TIMESTAMP(timezone=True), default=datetime.now)

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:  # pytlint: disable=all
        return mapped_column(TIMESTAMP(timezone=True), default=datetime.now)
