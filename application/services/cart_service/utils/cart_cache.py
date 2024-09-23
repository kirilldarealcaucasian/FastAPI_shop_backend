from functools import wraps
from typing import Callable
from uuid import UUID

from aioredis import Redis
from application.schemas import ReturnCartS
from application.schemas.order_schemas import AssocBookS
from .cart_converter import serialize_and_store_cart_books

from core.exceptions import NoCookieError
from infrastructure.redis import redis_client
from logger import logger


def get_cart_from_cache(func: Callable):
    from application.services.cart_service.utils import deserialize_cart

    @wraps(func)
    async def wrapper(
            *args, **kwargs,
    ):
        """
            iterates over set of book_ids in redis-set, for each book_id
            retrieves its metadata from redis-hash and constructs ReturnCartS
        """
        redis_con: Redis = redis_client.connection
        if not redis_con:
            logger.error(
                msg="Redis connection error in get_cart_from_cache, failed to retrieve cart from cache"
            )
            return await func(*args, **kwargs)

        shopping_session_id = kwargs["shopping_session_id"]

        if not shopping_session_id:
            raise NoCookieError("No shopping_session_id in the cookie")

        cart_set_name = f"cart:{shopping_session_id}"  # name of a set where book_ids are stored

        cart_exists = await redis_con.exists(cart_set_name)

        if not cart_exists:
            logger.debug("Cart doesn't exist, call function directly")
            return await func(*args, **kwargs)

        logger.debug("Cart exists, read data from redis")

        books_id: list[str] = await redis_con.smembers(
            name=cart_set_name
        )  # get list of book_ids stored in the cart from redis set

        deserialized_cart_books: list[AssocBookS] = []
        for book_id in books_id:
            book_metadata_hash = f"book:{book_id}"
            book_metadata_keys = await redis_con.hkeys(name=book_metadata_hash)
            book_metadata_values = await redis_con.hvals(name=book_metadata_hash)
            deserialized_book: AssocBookS = deserialize_cart(
                book_metadata_keys=book_metadata_keys,
                book_metadata_values=book_metadata_values
            )
            deserialized_cart_books.append(deserialized_book)

        return ReturnCartS(
            cart_id=shopping_session_id,
            books=deserialized_cart_books
        )
    return wrapper


def store_cart_to_cache(cache_time_seconds: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_con: Redis = redis_client.connection
            assembled_cart: ReturnCartS = await func(*args, **kwargs)
            if not redis_con:
                logger.error(
                    msg="Redis connection error in store_cart_to_cache, failed to store cart in cache"
                )
                return assembled_cart

            shopping_session_id: UUID = assembled_cart.cart_id

            books_ids = set()  # set of book_ids will be stored in redis
            for book in assembled_cart.books:
                await serialize_and_store_cart_books(
                    book=book,
                    redis_con=redis_con
                )
                books_ids.add(str(book.book_id))
                book_hash_name = f"book:{book.book_id}"
                await redis_con.expire(
                    name=book_hash_name,
                    time=cache_time_seconds,
                )  # set expire timeout for book_hash

            for book_id in books_ids:
                cart_set_name = f"cart:{shopping_session_id}"
                await redis_con.sadd(
                    cart_set_name,
                    book_id
                )
                await redis_con.expire(
                    name=f"cart:{assembled_cart.cart_id}",
                    time=cache_time_seconds
                )  # set expire timeout for redis-set of books

            logger.info("Successfully stored data in cache")
            return assembled_cart
        return wrapper
    return decorator