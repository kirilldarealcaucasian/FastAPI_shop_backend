import os
from pathlib import Path
import tempfile
from datetime import date, datetime

from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq

from .config import settings
from .db import iter_aggregated_features
from .s3 import FEATURES_SCHEMA, s3_parquet_client


def build_object_name(target_date: date) -> str:
    prefix = settings.S3_OBJECT_PREFIX.strip("/")
    return f"{prefix}/event_date={target_date.isoformat()}/features.parquet"


async def run_once(target_date: date, start_dt: datetime, end_dt: datetime) -> None:
    object_name = build_object_name(target_date=target_date)
    writer: pq.ParquetWriter | None = None
    total_rows = 0
    batch_count = 0

    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".parquet",
        delete=False,
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        writer = pq.ParquetWriter(str(tmp_path), FEATURES_SCHEMA, compression="snappy")

        async for batch in iter_aggregated_features(
            target_start=start_dt,
            target_end=end_dt,
            batch_size=settings.ETL_BATCH_SIZE,
        ):
            table = pa.Table.from_pylist(batch, schema=FEATURES_SCHEMA)
            writer.write_table(table)
            total_rows += table.num_rows
            batch_count += 1

        writer.close()
        writer = None

        if total_rows == 0:
            logger.info(
                "No interaction events for target date; uploading empty parquet",
                extra={"target_date": target_date.isoformat(), "object_name": object_name},
            )

        await s3_parquet_client.upload_file(
            object_name=object_name,
            file_path=str(tmp_path),
        )
    finally:
        if writer is not None:
            writer.close()
        if tmp_path.exists():
            os.remove(tmp_path)

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
