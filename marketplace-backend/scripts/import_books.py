from __future__ import annotations

import argparse
import asyncio
import csv
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.sql.schema import Table
from application.settings import settings  # noqa: E402


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "marketplace-backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


AUTHOR_SPLIT_PATTERN = re.compile(r"\s*(?:\||;|&| and )\s*", re.IGNORECASE)
CATEGORY_SPLIT_PATTERN = re.compile(r"\s*(?:\||;|&|/)\s*")


@dataclass(slots=True)
class ImportStats:
    total_rows: int = 0
    books_inserted: int = 0
    books_updated: int = 0
    categories_inserted: int = 0
    authors_inserted: int = 0
    book_category_links_inserted: int = 0
    book_author_links_inserted: int = 0
    skipped_rows: int = 0


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def split_multi_value(value: str, pattern: re.Pattern[str]) -> list[str]:
    if not value:
        return []
    parts = [normalize_text(part) for part in pattern.split(value)]
    deduplicated: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        lowered = part.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduplicated.append(part)
    return deduplicated


def parse_int(value: str | None, default: int = 0) -> int:
    raw = normalize_text(value)
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def parse_decimal(value: str | None, default: Decimal = Decimal("0")) -> Decimal:
    raw = normalize_text(value)
    if not raw:
        return default
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return default


def table_key(table_name: str) -> str:
    if settings.DB_SCHEMA:
        return f"{settings.DB_SCHEMA}.{table_name}"
    return table_name


def get_table(metadata: MetaData, table_name: str) -> Table:
    key = table_key(table_name)
    table = metadata.tables.get(key)
    if table is None:
        raise RuntimeError(f"Table `{key}` not found in database metadata.")
    return table


async def reflect_required_tables(conn: AsyncConnection) -> dict[str, Table]:
    metadata = MetaData(schema=settings.DB_SCHEMA)
    required_tables = [
        "books",
        "authors",
        "categories",
        "book_author_assoc",
        "book_category_assoc",
    ]
    await conn.run_sync(
        lambda sync_conn: metadata.reflect(
            bind=sync_conn,
            schema=settings.DB_SCHEMA,
            only=required_tables,
        )
    )
    return {name: get_table(metadata, name) for name in required_tables}


def validate_tables(tables: dict[str, Table]) -> None:
    books = tables["books"]
    authors = tables["authors"]
    categories = tables["categories"]
    book_author_assoc = tables["book_author_assoc"]
    book_category_assoc = tables["book_category_assoc"]

    if "id" not in books.c or "isbn" not in books.c:
        raise RuntimeError("`books` table must include `id` and `isbn` columns.")
    if "id" not in authors.c or "name" not in authors.c:
        raise RuntimeError("`authors` table must include `id` and `name` columns.")
    if "id" not in categories.c or "name" not in categories.c:
        raise RuntimeError("`categories` table must include `id` and `name` columns.")
    if "book_id" not in book_author_assoc.c or "author_id" not in book_author_assoc.c:
        raise RuntimeError(
            "`book_author_assoc` table must include `book_id` and `author_id`."
        )
    if (
        "book_id" not in book_category_assoc.c
        or "category_id" not in book_category_assoc.c
    ):
        raise RuntimeError(
            "`book_category_assoc` table must include `book_id` and `category_id`."
        )


def build_book_payload(
    row: dict[str, str], books_table: Table, now: datetime
) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if "isbn" in books_table.c:
        payload["isbn"] = normalize_text(row.get("isbn"))
    if "rating" in books_table.c:
        payload["rating"] = float(parse_decimal(row.get("rating")))
    if "name" in books_table.c:
        payload["name"] = normalize_text(row.get("name"))
    if "year_of_publication" in books_table.c:
        payload["year_of_publication"] = parse_int(row.get("year_of_publication"))
    if "publisher" in books_table.c:
        payload["publisher"] = normalize_text(row.get("publisher"))
    if "image" in books_table.c:
        payload["image"] = normalize_text(row.get("image"))
    if "summary" in books_table.c:
        summary = row.get("summary")
        payload["summary"] = summary.strip() if summary else None
    if "language" in books_table.c:
        payload["language"] = normalize_text(row.get("language"))
    if "country" in books_table.c:
        payload["country"] = normalize_text(row.get("country"))
    if "price_per_unit" in books_table.c:
        payload["price_per_unit"] = parse_decimal(row.get("price"))
    if "number_in_stock" in books_table.c:
        payload["number_in_stock"] = parse_int(row.get("number_in_stock"))
    if "created_at" in books_table.c:
        payload["created_at"] = now
    if "updated_at" in books_table.c:
        payload["updated_at"] = now
    return payload


async def get_or_create_category_id(
    conn: AsyncConnection,
    categories_table: Table,
    existing_categories: dict[str, int],
    category_name: str,
) -> tuple[int | None, bool]:
    cached_id = existing_categories.get(category_name.casefold())
    if cached_id is not None:
        return cached_id, False

    category_id = await conn.scalar(
        select(categories_table.c.id).where(categories_table.c.name == category_name)
    )
    if category_id is None:
        category_id = await conn.scalar(
            pg_insert(categories_table)
            .values(name=category_name)
            .returning(categories_table.c.id)
        )
        was_inserted = category_id is not None
    else:
        was_inserted = False
    if category_id is not None:
        existing_categories[category_name.casefold()] = category_id
    return category_id, was_inserted


async def get_or_create_author_id(
    conn: AsyncConnection,
    authors_table: Table,
    existing_authors: dict[str, int],
    author_name: str,
) -> tuple[int | None, bool]:
    cached_id = existing_authors.get(author_name.casefold())
    if cached_id is not None:
        return cached_id, False

    author_id = await conn.scalar(
        select(authors_table.c.id).where(authors_table.c.name == author_name)
    )
    if author_id is None:
        author_id = await conn.scalar(
            pg_insert(authors_table)
            .values(name=author_name)
            .returning(authors_table.c.id)
        )
        was_inserted = author_id is not None
    else:
        was_inserted = False
    if author_id is not None:
        existing_authors[author_name.casefold()] = author_id
    return author_id, was_inserted


async def import_books(csv_path: Path) -> ImportStats:
    stats = ImportStats()
    engine: AsyncEngine = create_async_engine(settings.get_db_url, echo=False)

    try:
        async with engine.begin() as conn:
            tables = await reflect_required_tables(conn)
            validate_tables(tables)

            books_table = tables["books"]
            authors_table = tables["authors"]
            categories_table = tables["categories"]
            book_author_assoc = tables["book_author_assoc"]
            book_category_assoc = tables["book_category_assoc"]

            existing_books: dict[str, int] = {
                row.isbn: row.id
                for row in (
                    await conn.execute(select(books_table.c.id, books_table.c.isbn))
                ).all()
                if row.isbn
            }
            existing_authors: dict[str, int] = {
                row.name.casefold(): row.id
                for row in (
                    await conn.execute(select(authors_table.c.id, authors_table.c.name))
                ).all()
                if row.name
            }
            existing_categories: dict[str, int] = {
                row.name.casefold(): row.id
                for row in (
                    await conn.execute(
                        select(categories_table.c.id, categories_table.c.name)
                    )
                ).all()
                if row.name
            }

            with csv_path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    stats.total_rows += 1

                    isbn = normalize_text(row.get("isbn"))
                    if not isbn:
                        stats.skipped_rows += 1
                        continue

                    now = datetime.now(timezone.utc)
                    book_payload = build_book_payload(row, books_table, now)

                    if isbn in existing_books:
                        book_id = existing_books[isbn]
                        update_payload = {
                            key: value
                            for key, value in book_payload.items()
                            if key not in {"isbn", "created_at"}
                        }
                        await conn.execute(
                            update(books_table)
                            .where(books_table.c.id == book_id)
                            .values(**update_payload)
                        )
                        stats.books_updated += 1
                    else:
                        book_id = await conn.scalar(
                            pg_insert(books_table)
                            .values(**book_payload)
                            .returning(books_table.c.id)
                        )
                        if book_id is None:
                            stats.skipped_rows += 1
                            continue
                        existing_books[isbn] = book_id
                        stats.books_inserted += 1

                    category_names = split_multi_value(
                        normalize_text(row.get("category")),
                        CATEGORY_SPLIT_PATTERN,
                    )
                    for category_name in category_names:
                        category_id, was_inserted = await get_or_create_category_id(
                            conn=conn,
                            categories_table=categories_table,
                            existing_categories=existing_categories,
                            category_name=category_name,
                        )
                        if was_inserted:
                            stats.categories_inserted += 1
                        if category_id is None:
                            continue

                        result = await conn.execute(
                            pg_insert(book_category_assoc)
                            .values(book_id=book_id, category_id=category_id)
                            .on_conflict_do_nothing()
                        )
                        if result.rowcount and result.rowcount > 0:
                            stats.book_category_links_inserted += result.rowcount

                    author_names = split_multi_value(
                        normalize_text(row.get("book_author")),
                        AUTHOR_SPLIT_PATTERN,
                    )
                    for author_name in author_names:
                        author_id, was_inserted = await get_or_create_author_id(
                            conn=conn,
                            authors_table=authors_table,
                            existing_authors=existing_authors,
                            author_name=author_name,
                        )
                        if was_inserted:
                            stats.authors_inserted += 1
                        if author_id is None:
                            continue

                        result = await conn.execute(
                            pg_insert(book_author_assoc)
                            .values(book_id=book_id, author_id=author_id)
                            .on_conflict_do_nothing()
                        )
                        if result.rowcount and result.rowcount > 0:
                            stats.book_author_links_inserted += result.rowcount
    finally:
        await engine.dispose()

    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import books from CSV into books/authors/categories and association tables."
        )
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT_DIR / "scripts" / "books.csv",
        help="Path to CSV file. Default: scripts/books.csv",
    )
    return parser.parse_args()


async def _main() -> None:
    args = parse_args()
    csv_path: Path = args.csv
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    stats = await import_books(csv_path=csv_path)
    print(
        "Import completed. "
        f"rows={stats.total_rows}, "
        f"books_inserted={stats.books_inserted}, "
        f"books_updated={stats.books_updated}, "
        f"categories_inserted={stats.categories_inserted}, "
        f"authors_inserted={stats.authors_inserted}, "
        f"book_category_links_inserted={stats.book_category_links_inserted}, "
        f"book_author_links_inserted={stats.book_author_links_inserted}, "
        f"skipped_rows={stats.skipped_rows}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
