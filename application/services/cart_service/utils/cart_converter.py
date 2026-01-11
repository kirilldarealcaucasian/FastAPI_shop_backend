import json

from aioredis import DataError, Redis
from asyncpg.pgproto.pgproto import UUID as pgproto_UUID

from application.schemas.order_schemas import AssocBookS


async def serialize_and_store_cart_books(book: AssocBookS, redis_con: Redis):
    """serializes book metadata and stores it to redis"""
    book_to_dict: dict = book.model_dump(exclude_none=True)
    for key, value in book_to_dict.items():
        # create hash for books metadata
        try:
            await redis_con.hset(name=f"book:{book.book_id}", key=key, value=value)
        except DataError:
            # if any field is unserializable, we convert it to
            # its string representation
            value_to_str = (
                str(value) if type(value) is pgproto_UUID else json.dumps(value)
            )

            await redis_con.hset(
                name=f"book:{book.book_id}", key=key, value=value_to_str
            )


def deserialize_cart(
    book_metadata_keys: list[str], book_metadata_values: list[str]
) -> AssocBookS:
    book_metadata = dict(zip(book_metadata_keys, book_metadata_values))

    authors = book_metadata["authors"]
    categories = book_metadata["categories"]

    authors_deserialized: list[str] = json.loads(authors)  # deserializes  list
    categories_deserialized: list[str] = json.loads(categories)  # deserializes  list

    del book_metadata["authors"]  # deletes serialized list of authors
    del book_metadata["categories"]  # deletes serialized list of categories

    return AssocBookS(
        **book_metadata,
        authors=authors_deserialized,
        categories=categories_deserialized,
    )
