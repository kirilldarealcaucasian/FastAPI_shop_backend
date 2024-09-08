from pydantic import BaseModel, UUID4, Field

from core.exceptions import DecrementNumberInStockError


class BookS(BaseModel, validate_assignment=True):
    id: UUID4 | None = None
    isbn: str | None = None
    name: str | None = None
    description: str | None = None
    price_per_unit: float | None = None
    number_in_stock: int | None = None
    category_id: int | None = None
    rating: float | None = None
    discount: int | None = None
    price_with_discount: float | None = Field(
        default=lambda model: model.price_per_unit - (model.discount * 0.01) * model.price_per_unit
    )

    def decrement_number_in_stock(self, val: int):
        if self.number_in_stock - val < 0:
            raise DecrementNumberInStockError(
                info="You're trying to order more books that available"
            )
        self.number_in_stock -= val

    def increment_number_in_stock(self, val: int):
        self.number_in_stock += val
