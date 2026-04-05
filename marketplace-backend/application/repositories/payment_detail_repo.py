from typing import Protocol, Type, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PaymentDetail
from .orm_entity_repo import OrmEntityRepoInterface, OrmEntityRepository
from shared_lib.exceptions import DBError, NotFoundError


class PaymentDetailRepoInterface(Protocol):

    async def get_by_id(
            self,
            session: AsyncSession,
            id: UUID
    ) -> PaymentDetail:
        ...


CombinedPaymentDetailRepoInterface = Union[
    PaymentDetailRepoInterface, OrmEntityRepoInterface]


class PaymentDetailRepository(OrmEntityRepository):
    @property
    def model(self) -> Type[PaymentDetail]:
        return PaymentDetail

    async def get_by_id(
            self,
            session: AsyncSession,
            id: UUID
    ) -> PaymentDetail:
        stmt = select(PaymentDetail).where(PaymentDetail.id == str(id))

        try:
            res: Union[PaymentDetail, None] = (await session.scalars(stmt)).one_or_none()
        except SQLAlchemyError as e:
            raise DBError(traceback=str(e))

        if not res:
            raise NotFoundError(entity="PaymentDetail")

        return res
