from typing import TypeVar

__all__ = ("format_for_deletion",)



T = TypeVar("T")


def format_for_deletion(
    objects: list[T], bucket_name: str
) -> list[dict[str, str]]:
    # constructs url to access obj in S3 bucket.

    return [
        {"Key": "/".join([bucket_name, obj.url.split("/")[-1]])}
        for obj in objects
    ]
