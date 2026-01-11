from pydantic import BaseModel, ConfigDict

from core.exceptions import DecrementNumberInStockError


class BookS(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    name: str
    description: str
    price_per_unit: float
    number_in_stock: int
    category_id: int
    rating: float
    discount: int

    def decrement_number_in_stock(self, quantity: int):
        if self.number_in_stock > quantity:  # type: ignore
            raise DecrementNumberInStockError(
                info="You're trying to order more books that available"
            )
        self.number_in_stock -= quantity

    def increment_number_in_stock(self, quantity: int):
        self.number_in_stock += quantity

    def is_enough_in_stock(self, quantity: int) -> bool:
        return self.number_in_stock >= quantity
