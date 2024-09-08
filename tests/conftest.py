import json
from typing import Generator
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import insert

from infrastructure.postgres import db_client
from application.models import Base, User, Book, BookOrderAssoc, Author, Publisher, Order, Image, Category, \
    BookCategoryAssoc, CartItem, ShoppingSession
from application.cmd import app
from datetime import datetime
import os



@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    # assert settings.MODE == "TEST"

    async with db_client.engine.begin() as con:
        await con.run_sync(Base.metadata.drop_all)
        await con.run_sync(Base.metadata.create_all)

    def open_test_data_json(model: str) -> dict:
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
    images: dict = open_test_data_json("images")
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
        BookOrderAssoc, BookCategoryAssoc, Image,
        ShoppingSession, CartItem
    ]

    db_to_add_data = [
        users, books, orders,
        authors, publishers, categories,
        book_order_assoc, book_category_assoc, images,
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

