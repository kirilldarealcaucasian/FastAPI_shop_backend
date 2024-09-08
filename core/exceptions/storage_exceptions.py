class DuplicateError(Exception):
    def __init__(self, entity, traceback: str | None = None):
        self.entity = entity
        self.traceback = traceback

    def __str__(self):
        return f"{self.entity} already exists, {self.traceback}"


class DBError(Exception):
    def __init__(self, traceback: str = ""):
        self.traceback = traceback

    def __str__(self):
        return f"Traceback: {self.traceback}"


class NotFoundError(Exception):

    def __init__(self, entity="Entity"):
        self.entity = entity

    def __str__(self):
        return f"{self.entity} wasn't found"


class DeletionError(Exception):
    def __init__(self, entity):
        self.entity = entity

    def __str__(self):
        return f"Failed to delete {self.entity}"


class RemoteBucketDeletionError(Exception):

    def __str__(self):
        return "Failed to delete image from the remote bucket"
