

class DeleteBooksFromCartError(Exception):

    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to delete book(s) from cart: {self.info}"


class DeleteBooksFromOrderError(Exception):

    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to delete book(s) from order: {self.info}"


class AddBooksToCartError(Exception):
    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to add book(s) to cart: {self.info}"


class AddBookToOrderError(Exception):
    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"Failed to add book(s) to order: {self.info}"


class DecrementNumberInStockError(Exception):
    def __init__(self, info: str):
        self.info = info

    def __str__(self):
        return f"{self.info}"
