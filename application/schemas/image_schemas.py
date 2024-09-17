from application.schemas.base_schemas import ImageBaseS


class ReturnImageS(ImageBaseS):
    id: int
    book_id: str
    url: str


class CreateImageS(ImageBaseS):
    book_id: str
    url: str