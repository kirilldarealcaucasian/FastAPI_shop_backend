from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from application.schemas import ReturnImageS
from infrastructure.postgres import db_client
from application.services import ImageService


router = APIRouter(prefix="/v1/images/books", tags=["Images"])


@router.get(
    "/{book_isbn}",
    status_code=status.HTTP_200_OK,
    response_model=list[ReturnImageS]
)
async def get_all_images(
        book_id: UUID,
        service: ImageService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
):
    return await service.get_all_images(session=session, book_id=book_id)


@router.post('/{book_isbn}', status_code=status.HTTP_201_CREATED)
async def create_image(
        book_id: UUID,
        file: UploadFile = File(...),
        service: ImageService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
) -> None:
    return await service.upload_image(
        session=session,
        image=file,
        book_id=book_id
    )


@router.delete('/{image_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
        image_id: int,
        service: ImageService = Depends(),
        session: AsyncSession = Depends(db_client.get_scoped_session_dependency)
) -> None:
    return await service.delete_image(session=session,
                                      image_id=image_id,
                                      )
