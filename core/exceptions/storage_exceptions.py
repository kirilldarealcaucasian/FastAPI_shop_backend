class DuplicateError(BaseException):
    def __init__(self, entity):
        self.entity = entity

    def __str__(self):
        return f"{self.entity} already exists"


class DBError(BaseException):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return f"{self.message}"


class NotFoundError(BaseException):
    def __init__(self, entity):
        self.entity = entity

    def __str__(self):
        return f"{self.entity} wasn't found"