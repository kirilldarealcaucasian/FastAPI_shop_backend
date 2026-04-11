from datetime import date, datetime
from typing import Any

from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq

from .config import settings
from .db import iter_aggregated_features
from .s3 import FEATURES_SCHEMA, s3_parquet_client

MIN_MULTIPART_SIZE_BYTES = 5 * 1024 * 1024


def build_object_name(target_date: date) -> str:
    prefix = settings.S3_OBJECT_PREFIX.strip("/")
    return f"{prefix}/event_date={target_date.isoformat()}/features.parquet"


def _rows_to_pydict(rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {
        field.name: [row.get(field.name) for row in rows] for field in FEATURES_SCHEMA
    }


class _ChunkedParquetBuffer:
    def __init__(self) -> None:
        self._buf = bytearray()
        self._position = 0

    def write(self, data: bytes) -> int:
        self._buf.extend(data)
        self._position += len(data)
        return len(data)

    def tell(self) -> int:
        return self._position

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None

    def pop_full_chunks(self, chunk_size: int) -> list[bytes]:
        chunks: list[bytes] = []
        while len(self._buf) >= chunk_size:
            chunks.append(bytes(self._buf[:chunk_size]))
            del self._buf[:chunk_size]
        return chunks

    def pop_remaining(self) -> bytes:
        payload = bytes(self._buf)
        self._buf.clear()
        return payload


async def _upload_ready_parts(
    *,
    object_name: str,
    upload_id: str,
    buffer: _ChunkedParquetBuffer,
    part_size: int,
    parts: list[dict[str, str | int]],
    part_number: int,
    final: bool,
) -> int:
    for chunk in buffer.pop_full_chunks(part_size):
        etag = await s3_parquet_client.upload_part(
            object_name=object_name,
            upload_id=upload_id,
            part_number=part_number,
            payload=chunk,
        )
        parts.append({"ETag": etag, "PartNumber": part_number})
        part_number += 1

    if final:
        remaining = buffer.pop_remaining()
        if remaining:
            etag = await s3_parquet_client.upload_part(
                object_name=object_name,
                upload_id=upload_id,
                part_number=part_number,
                payload=remaining,
            )
            parts.append({"ETag": etag, "PartNumber": part_number})
            part_number += 1

    return part_number


async def run_once(target_date: date, start_dt: datetime, end_dt: datetime) -> None:
    object_name = build_object_name(target_date=target_date)
    part_size = max(
        settings.ETL_S3_MULTIPART_PART_SIZE_BYTES,
        MIN_MULTIPART_SIZE_BYTES,
    )
    buffer = _ChunkedParquetBuffer()
    upload_id = await s3_parquet_client.create_multipart_upload(object_name=object_name)
    parts: list[dict[str, str | int]] = []
    part_number = 1
    total_rows = 0
    batch_count = 0

    try:
        with pq.ParquetWriter(buffer, FEATURES_SCHEMA, compression="snappy") as writer:
            async for batch in iter_aggregated_features(
                target_start=start_dt,
                target_end=end_dt,
                batch_size=settings.ETL_BATCH_SIZE,
            ):
                table = pa.Table.from_pydict(
                    _rows_to_pydict(batch),
                    schema=FEATURES_SCHEMA,
                )
                writer.write_table(table)
                total_rows += table.num_rows
                batch_count += 1

                part_number = await _upload_ready_parts(
                    object_name=object_name,
                    upload_id=upload_id,
                    buffer=buffer,
                    part_size=part_size,
                    parts=parts,
                    part_number=part_number,
                    final=False,
                )

        part_number = await _upload_ready_parts(
            object_name=object_name,
            upload_id=upload_id,
            buffer=buffer,
            part_size=part_size,
            parts=parts,
            part_number=part_number,
            final=True,
        )

        if total_rows == 0:
            logger.info(
                "No interaction events for target date; uploading empty parquet",
                extra={
                    "target_date": target_date.isoformat(),
                    "object_name": object_name,
                },
            )

        await s3_parquet_client.complete_multipart_upload(
            object_name=object_name,
            upload_id=upload_id,
            parts=parts,
        )
    except Exception:
        await s3_parquet_client.abort_multipart_upload(
            object_name=object_name,
            upload_id=upload_id,
        )
        raise

    logger.info(
        "Daily training features ETL completed",
        extra={
            "target_date": target_date.isoformat(),
            "rows": total_rows,
            "batches": batch_count,
            "bucket": settings.S3_BUCKET,
            "object_name": object_name,
        },
    )
