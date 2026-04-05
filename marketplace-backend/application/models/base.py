from sqlalchemy import BIGINT, Double, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from ..settings import settings

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class BaseWithoutId(DeclarativeBase):
    __abstract__ = True
    __allow_unmapped__ = True

    metadata = MetaData(naming_convention=convention, schema=settings.DB_SCHEMA)
    type_annotation_map = {int: BIGINT, float: Double}

    @declared_attr.directive
    def __tablename__(self):
        return f"{self.__name__.lower()}s"


class Base(BaseWithoutId):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
