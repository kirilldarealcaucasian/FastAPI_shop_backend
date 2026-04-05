"""
Usage:
  python price_enrich_bookcrossing.py \
    --books-csv BX-Books.csv \
    --out prices.jsonl \
    --max 5000 \
    --sleep 0.12

Input expectations:
  - CSV contains a column named "ISBN"
  - Optional column: "Year-Of-Publication" (used for fallback estimation)

Output:
  JSONL (append-only), each line:
  { "isbn": "<isbn13>", "price": <number> }
  Resume behavior:
  - If output file already exists, processed ISBNs are loaded and skipped.
  - New rows are appended in batches, so restarts continue where interrupted.
"""

from __future__ import annotations

import asyncio
import argparse
import csv
import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

LOGGER = logging.getLogger(__name__)


# -----------------------------
# ISBN normalization utilities
# -----------------------------

_ISBN_CLEAN_RE = re.compile(r"[^0-9Xx]")


def clean_isbn(raw: str) -> str:
    return _ISBN_CLEAN_RE.sub("", (raw or "").strip())


def is_valid_isbn10(isbn10: str) -> bool:
    if len(isbn10) != 10:
        return False
    if not re.fullmatch(r"\d{9}[\dXx]", isbn10):
        return False

    total = 0
    for i, ch in enumerate(isbn10[:9], start=1):
        total += i * int(ch)
    check = total % 11
    expected = "X" if check == 10 else str(check)
    return expected == isbn10[-1].upper()


def isbn10_to_isbn13(isbn10: str) -> str:
    """Convert valid ISBN-10 to ISBN-13 with 978 prefix."""
    core = "978" + isbn10[:9]
    # ISBN-13 check digit
    s = 0
    for i, ch in enumerate(core, start=1):
        d = int(ch)
        s += d if i % 2 == 1 else 3 * d
    check = (10 - (s % 10)) % 10
    return core + str(check)


def is_valid_isbn13(isbn13: str) -> bool:
    if len(isbn13) != 13 or not isbn13.isdigit():
        return False
    s = 0
    for i, ch in enumerate(isbn13[:12], start=1):
        d = int(ch)
        s += d if i % 2 == 1 else 3 * d
    check = (10 - (s % 10)) % 10
    return check == int(isbn13[-1])


def normalize_to_isbn13(raw: str) -> Optional[str]:
    x = clean_isbn(raw)
    if len(x) == 13 and x.isdigit() and is_valid_isbn13(x):
        return x
    if len(x) == 10 and is_valid_isbn10(x):
        return isbn10_to_isbn13(x.upper())
    return None


# -----------------------------
# Pricing (Google Books + fallback)
# -----------------------------


def fetch_google_books_price(isbn13: str, timeout: float = 10.0) -> Optional[float]:
    """
    Synchronous API request helper. Called from async workflow via asyncio.to_thread.
    """
    return _fetch_google_books_price_sync(isbn13=isbn13, timeout=timeout)


def _fetch_google_books_price_sync(
    isbn13: str, timeout: float = 10.0
) -> Optional[float]:
    """
    Returns a numeric retail/list price if available, else None.

    Google Books often returns no price (saleability NOT_FOR_SALE), or ebook-only.
    We'll check common fields in saleInfo.
    """
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"isbn:{isbn13}"}
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    items = data.get("items") or []
    if not items:
        return None

    # Try best candidate first item; you could improve matching by checking volumeInfo industryIdentifiers.
    sale = items[0].get("saleInfo") or {}
    # Prefer retailPrice, then listPrice
    for key in ("retailPrice", "listPrice"):
        pr = sale.get(key)
        if isinstance(pr, dict) and "amount" in pr:
            try:
                return float(pr["amount"])
            except Exception:
                pass

    return None


async def fetch_google_books_price_async(
    isbn13: str, timeout: float = 10.0
) -> Optional[float]:
    return await asyncio.to_thread(fetch_google_books_price, isbn13, timeout)


def current_utc_year() -> int:
    return datetime.now(UTC).year


def fallback_estimate_price(year: Optional[int]) -> float:
    """
    Simple, stable heuristic:
      base_price = 20
      age_discount = 0.6^(age/10)
      clamp to [2, 60]
    """
    base = 20.0
    now_year = current_utc_year()
    if year is None or year < 1400 or year > now_year + 1:
        year = None

    if year is None:
        price = base * 0.7  # generic fallback
    else:
        age = max(0, now_year - year)
        price = base * (0.6 ** (age / 10.0))

    # Clamp
    price = max(2.0, min(60.0, price))
    # Round to 2 decimals
    return float(f"{price:.2f}")


# -----------------------------
# Main script
# -----------------------------


def parse_int(x: str) -> Optional[int]:
    try:
        return int(str(x).strip())
    except Exception:
        return None


def load_books(
    csv_path: str, max_rows: Optional[int]
) -> List[Tuple[str, Optional[int]]]:
    """
    Returns list of (raw_isbn, year) from CSV.
    """
    books: List[Tuple[str, Optional[int]]] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        raw_fields = reader.fieldnames or []
        normalized_to_raw = {field.strip().lower(): field for field in raw_fields}
        delimiter = getattr(dialect, "delimiter", ",")

        isbn_col = normalized_to_raw.get("isbn")
        if not isbn_col:
            raise ValueError(f'CSV missing required column "isbn". Found: {raw_fields}')

        year_col = normalized_to_raw.get(
            "year-of-publication"
        ) or normalized_to_raw.get("year_of_publication")
        LOGGER.info(
            "CSV parsed: path=%s delimiter=%r isbn_col=%s year_col=%s",
            csv_path,
            delimiter,
            isbn_col,
            year_col or "<none>",
        )

        for row in reader:
            raw_isbn = (row.get(isbn_col) or "").strip()
            year = parse_int((row.get(year_col) or "") if year_col else "")
            books.append((raw_isbn, year))
            if max_rows is not None and len(books) >= max_rows:
                break
    return books


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


async def build_price_for_isbn(
    isbn13: str,
    year: Optional[int],
    no_api: bool,
    timeout: float,
    sleep_seconds: float,
    semaphore: asyncio.Semaphore,
) -> Tuple[Dict[str, Any], str]:
    price: Optional[float] = None
    source = "fallback"

    async with semaphore:
        if not no_api:
            try:
                price = await fetch_google_books_price_async(
                    isbn13=isbn13, timeout=timeout
                )
            except requests.RequestException as exc:
                LOGGER.debug("Google Books request failed for %s: %s", isbn13, exc)
            except Exception as exc:  # noqa: BLE001
                LOGGER.debug("Unexpected error for %s: %s", isbn13, exc)

            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)

    if price is not None:
        source = "google_books"
    else:
        price = fallback_estimate_price(year)

    return {"isbn": isbn13, "price": float(price)}, source


def load_processed_isbns(out_path: str) -> Set[str]:
    """
    Supports:
    - JSONL: one JSON object per line
    - JSON array (legacy format): [{...}, {...}]
    """
    processed: Set[str] = set()
    if not os.path.exists(out_path):
        return processed

    try:
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for row in data:
                if isinstance(row, dict):
                    isbn = str(row.get("isbn") or "").strip()
                    if isbn:
                        processed.add(isbn)
            LOGGER.info(
                "Resume scan loaded %s processed ISBNs from JSON array", len(processed)
            )
            return processed
    except json.JSONDecodeError:
        pass

    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                isbn = str(row.get("isbn") or "").strip()
                if isbn:
                    processed.add(isbn)

    LOGGER.info("Resume scan loaded %s processed ISBNs from JSONL", len(processed))
    return processed


def append_batch_jsonl(out_path: str, batch: List[Dict[str, Any]]) -> None:
    with open(out_path, "a", encoding="utf-8") as f:
        for row in batch:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--books-csv",
        required=True,
        help="Path to BX-Books.csv (or similar CSV with ISBN column)",
    )
    ap.add_argument(
        "--out",
        required=True,
        help="Output JSONL path (append-only, resumable)",
    )
    ap.add_argument(
        "--max", type=int, default=None, help="Max rows to process (for testing)"
    )
    ap.add_argument(
        "--sleep", type=float, default=0.12, help="Sleep between API calls (seconds)"
    )
    ap.add_argument(
        "--timeout", type=float, default=10.0, help="HTTP timeout per API request"
    )
    ap.add_argument(
        "--concurrency",
        type=int,
        default=25,
        help="Number of concurrent API requests",
    )
    ap.add_argument(
        "--progress-every",
        type=int,
        default=250,
        help="Log progress every N processed books",
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=300,
        help="Flush output to disk every N processed books",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    ap.add_argument(
        "--no-api",
        action="store_true",
        help="Skip Google Books API calls (fallback-only)",
    )
    args = ap.parse_args()
    configure_logging(args.log_level)
    LOGGER.info(
        "Starting price enrichment: books_csv=%s out=%s max=%s no_api=%s concurrency=%s sleep=%s timeout=%s",
        args.books_csv,
        args.out,
        args.max,
        args.no_api,
        args.concurrency,
        args.sleep,
        args.timeout,
    )
    LOGGER.info(
        "Output mode: append-only JSONL with resume support (batch_size=%s)",
        args.batch_size,
    )

    rows = load_books(args.books_csv, args.max)
    LOGGER.info("Loaded %s rows from CSV", len(rows))

    # Deduplicate by normalized ISBN13
    isbn_to_year: Dict[str, Optional[int]] = {}
    skipped = 0
    for raw_isbn, year in rows:
        isbn13 = normalize_to_isbn13(raw_isbn)
        if not isbn13:
            skipped += 1
            continue
        # Keep the earliest plausible year if multiple (helps avoid weird future years)
        if isbn13 not in isbn_to_year:
            isbn_to_year[isbn13] = year
        else:
            prev = isbn_to_year[isbn13]
            if prev is None:
                isbn_to_year[isbn13] = year
            elif (
                year is not None
                and 1400 <= year <= current_utc_year() + 1
                and year < prev
            ):
                isbn_to_year[isbn13] = year

    LOGGER.info(
        "ISBN normalization complete: unique_valid=%s skipped_invalid=%s",
        len(isbn_to_year),
        skipped,
    )

    if args.concurrency < 1:
        raise ValueError("--concurrency must be >= 1")
    if args.progress_every < 1:
        raise ValueError("--progress-every must be >= 1")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    processed_isbns = load_processed_isbns(args.out)
    pending_items: List[Tuple[str, Optional[int]]] = [
        (isbn13, year)
        for isbn13, year in isbn_to_year.items()
        if isbn13 not in processed_isbns
    ]
    LOGGER.info(
        "Resume state: already_done=%s remaining=%s",
        len(processed_isbns),
        len(pending_items),
    )
    if not pending_items:
        LOGGER.info("Nothing to do. All ISBNs already processed.")
        return

    semaphore = asyncio.Semaphore(args.concurrency)
    total = len(pending_items)
    item_iter = iter(pending_items)
    in_flight: Set[asyncio.Task[Tuple[Dict[str, Any], str]]] = set()
    pending_batch: List[Dict[str, Any]] = []
    api_count = 0
    fallback_count = 0
    written_now = 0

    def schedule_next() -> bool:
        try:
            isbn13, year = next(item_iter)
        except StopIteration:
            return False
        in_flight.add(
            asyncio.create_task(
                build_price_for_isbn(
                    isbn13=isbn13,
                    year=year,
                    no_api=args.no_api,
                    timeout=args.timeout,
                    sleep_seconds=args.sleep,
                    semaphore=semaphore,
                )
            )
        )
        return True

    for _ in range(min(args.concurrency, total)):
        schedule_next()

    idx = 0
    while in_flight:
        done, _ = await asyncio.wait(in_flight, return_when=asyncio.FIRST_COMPLETED)
        for finished in done:
            in_flight.remove(finished)
            row, source = await finished
            idx += 1
            pending_batch.append(row)
            written_now += 1

            if source == "google_books":
                api_count += 1
            else:
                fallback_count += 1

            if len(pending_batch) >= args.batch_size:
                append_batch_jsonl(args.out, pending_batch)
                LOGGER.info(
                    "Flushed batch: size=%s total_written_now=%s",
                    len(pending_batch),
                    written_now,
                )
                pending_batch = []

            if idx % args.progress_every == 0 or idx == total:
                LOGGER.info(
                    "Progress %s/%s | api=%s fallback=%s",
                    idx,
                    total,
                    api_count,
                    fallback_count,
                )

            schedule_next()

    if pending_batch:
        append_batch_jsonl(args.out, pending_batch)
        LOGGER.info(
            "Flushed final batch: size=%s total_written_now=%s",
            len(pending_batch),
            written_now,
        )

    LOGGER.info(
        "Done. Wrote %s new prices to %s. Existing before run: %s. Skipped invalid ISBN rows: %s. Sources this run: api=%s fallback=%s",
        written_now,
        args.out,
        len(processed_isbns),
        skipped,
        api_count,
        fallback_count,
    )


if __name__ == "__main__":
    asyncio.run(main())
