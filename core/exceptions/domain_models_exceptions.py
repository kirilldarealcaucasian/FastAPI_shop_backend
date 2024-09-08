

class DeleteBooksFromCartError(Exception):

    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to delete book(s) from cart: {self.info}"


class AddBooksToCartError(Exception):
    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to add book(s) to cart: {self.info}"


class DecrementNumberInStockError(Exception):
    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"{self.info}"
