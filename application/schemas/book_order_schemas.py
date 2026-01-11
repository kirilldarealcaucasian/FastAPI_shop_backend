from pydantic import BaseModel


class BookOrderPrimaryIdentifier(BaseModel):
    order_id: int
    book_id: int
