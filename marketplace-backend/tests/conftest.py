import asyncio
import json
import os
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
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
from application.models import (Author, Base, Book, BookAuthorsAssoc,
                                BookCategoryAssoc, BookOrderAssoc, CartItem,
                                Category, Order, ShoppingSession, User)
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

    test_data_dir = Path(__file__).resolve().parent / "test_data"

    def open_test_data_json(model: str) -> Mapping:
        with open(test_data_dir / f"{model}.json", "r", encoding="utf-8") as file:
            return json.load(file)

    users: dict = open_test_data_json("users")
    for user in users:
        first_name = user.pop("first_name", "")
        last_name = user.pop("last_name", "")
        user["name"] = f"{first_name} {last_name}".strip()

    books_raw: list[dict] = open_test_data_json("books")
    book_id_map: dict[str, int] = {
        str(book["id"]): idx for idx, book in enumerate(books_raw, start=1)
    }
    books: list[dict] = []
    for idx, book in enumerate(books_raw, start=1):
        books.append(
            {
                "id": idx,
                "isbn": book["isbn"],
                "name": book["name"],
                "year_of_publication": int(book.get("year_of_publication", 2020)),
                "publisher": str(book.get("publisher", "Test Publisher")),
                "image": str(book.get("image", "test.png")),
                "summary": book.get("summary", book.get("description")),
                "language": str(book.get("language", "EN")),
                "country": str(book.get("country", "US")),
                "price_per_unit": book["price_per_unit"],
                "number_in_stock": book["number_in_stock"],
                "rating": book.get("rating", 0),
                "discount": float(book.get("discount", 0)) / 100,
            }
        )

    orders: dict = open_test_data_json("orders")
    status_map = {"success": "done", "failed": "refund"}
    for order in orders:
        status = order.get("order_status")
        if status in status_map:
            order["order_status"] = status_map[status]
    authors_raw: list[dict] = open_test_data_json("authors")
    authors: list[dict] = []
    book_author_assoc: list[dict] = []
    for idx, author in enumerate(authors_raw, start=1):
        full_name = " ".join(
            part for part in [author.get("first_name", ""), author.get("last_name", "")] if part
        )
        authors.append({"id": idx, "name": full_name})
        mapped_book_id = book_id_map.get(str(author.get("book_id")))
        if mapped_book_id is not None:
            book_author_assoc.append({"book_id": mapped_book_id, "author_id": idx})

    categories: dict = open_test_data_json("categories")
    book_order_assoc: list[dict] = open_test_data_json("book_order_assoc")
    for order_item in book_order_assoc:
        order_item["book_id"] = book_id_map[str(order_item["book_id"])]

    book_category_assoc: list[dict] = open_test_data_json("book_category_assoc")
    for category_item in book_category_assoc:
        category_item["book_id"] = book_id_map[str(category_item["book_id"])]

    shopping_sessions: dict = open_test_data_json("shopping_sessions")
    cart_items: list[dict] = open_test_data_json("cart_items")
    for cart_item in cart_items:
        cart_item["book_id"] = book_id_map[str(cart_item["book_id"])]

    for session in shopping_sessions:
        """Convert a string to datetime"""

        session["expiration_time"]: datetime = datetime.strptime(
            session["expiration_time"],
            '%Y-%m-%d %H:%M:%S'
        )

    db_models = [
        User, Book, Order,
        Author, Category,
        BookOrderAssoc, BookCategoryAssoc, BookAuthorsAssoc,
        ShoppingSession, CartItem
    ]

    db_to_add_data = [
        users, books, orders,
        authors, categories,
        book_order_assoc, book_category_assoc, book_author_assoc,
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
