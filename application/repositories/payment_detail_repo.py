from typing import Protocol, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core import OrmEntityRepository
from application.models.models import PaymentDetail
from core.base_repos import OrmEntityRepoInterface
from core.exceptions import DBError, NotFoundError


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
    model: PaymentDetail = PaymentDetail

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
