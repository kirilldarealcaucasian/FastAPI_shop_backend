import asyncio
import json
import os
from collections.abc import Mapping
from datetime import datetime
from typing import Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import insert

# Required by Settings validation in Python 3.12 test runs.
os.environ.setdefault("LOCAL_POSTGRES_USER", "postgres")
os.environ.setdefault("LOCAL_POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("LOCAL_POSTGRES_SERVER", "localhost")
os.environ.setdefault("LOCAL_POSTGRES_PORT", "5432")
os.environ.setdefault("LOCAL_POSTGRES_DB", "shop_local")
os.environ.setdefault("YOOCASSA_ACCOUNT_ID", "1")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_HOURS", "1")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("JWT_ENCODE_ALGORITHM", "RS256")
os.environ.setdefault("JWT_DECODE_ALGORITHM", "RS256")
os.environ.setdefault("SALT", "test_salt")

from application.cmd import app
from application.models import (Author, Base, Book, BookCategoryAssoc,
                                BookOrderAssoc, CartItem, Category,
                                Order, Publisher, ShoppingSession, User)
from infrastructure.postgres import db_client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    # assert settings.MODE == "TEST"
    db_client.connect()

    try:
        async with db_client.engine.begin() as con:
            await con.run_sync(Base.metadata.drop_all)
            await con.run_sync(Base.metadata.create_all)
    except Exception as exc:
        pytest.skip(f"DB-dependent tests skipped: cannot prepare database ({exc})")

    def open_test_data_json(model: str) -> Mapping:
        with open(os.path.abspath(f"tests/test_data/{model}.json"), "r", encoding="utf-8") as file:
            return json.load(file)

    users: dict = open_test_data_json("users")
    books: dict = open_test_data_json("books")
    orders: dict = open_test_data_json("orders")
    authors: dict = open_test_data_json("authors")
    publishers: dict = open_test_data_json("publishers")
    categories: dict = open_test_data_json("categories")
    book_order_assoc: dict = open_test_data_json("book_order_assoc")
    book_category_assoc: dict = open_test_data_json("book_category_assoc")
    shopping_sessions: dict = open_test_data_json("shopping_sessions")
    cart_items: dict = open_test_data_json("cart_items")

    for session in shopping_sessions:
        """Convert a string to datetime"""

        session["expiration_time"]: datetime = datetime.strptime(
            session["expiration_time"],
            '%Y-%m-%d %H:%M:%S'
        )

    db_models = [
        User, Book, Order,
        Author, Publisher, Category,
        BookOrderAssoc, BookCategoryAssoc,
        ShoppingSession, CartItem
    ]

    db_to_add_data = [
        users, books, orders,
        authors, publishers, categories,
        book_order_assoc, book_category_assoc,
        shopping_sessions, cart_items
    ]

    async with db_client.async_session() as session:
        for model, data in zip(db_models, db_to_add_data):
            stmt = insert(model).values(data)
            await session.execute(stmt)
            await session.commit()


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
