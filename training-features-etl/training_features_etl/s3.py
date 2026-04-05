from contextlib import AsyncExitStack
from io import BytesIO
import os
from typing import Any

from aiobotocore.session import get_session
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq

from .config import settings

FEATURES_SCHEMA = pa.schema(
    [
        pa.field("subject_key", pa.string()),
        pa.field("item_id", pa.int64()),
        pa.field("view_cnt", pa.int32()),
        pa.field("long_view_cnt", pa.int32()),
        pa.field("cart_cnt", pa.int32()),
        pa.field("purchase_cnt", pa.int32()),
        pa.field("weight", pa.float32()),
        pa.field("first_event_ts", pa.timestamp("us")),
        pa.field("last_event_ts", pa.timestamp("us")),
        pa.field("event_date", pa.date32()),
    ]
)


class S3ParquetClient:
    def __init__(self) -> None:
        self._session = get_session()
        self._exit_stack: AsyncExitStack | None = None
        self._client: Any | None = None

    async def connect(self) -> Any | None:
        if self._client is not None:
            return self._client

        self._exit_stack = AsyncExitStack()
        try:
            self._client = await self._exit_stack.enter_async_context(
                self._session.create_client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    region_name=settings.S3_REGION,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                    use_ssl=settings.S3_SECURE,
                )
            )
            await self._ensure_bucket_exists()
            return self._client
        except (BotoCoreError, ClientError):
            logger.error(
                "Unable to connect to S3",
                extra={
                    "s3_endpoint": settings.S3_ENDPOINT_URL,
                    "s3_bucket": settings.S3_BUCKET,
                },
                exc_info=True,
            )
            if self._exit_stack is not None:
                await self._exit_stack.aclose()
            self._exit_stack = None
            self._client = None
            return None

    async def disconnect(self) -> None:
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self._client = None

    async def write_features_parquet(
        self,
        object_name: str,
        rows: list[dict[str, Any]],
    ) -> None:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        table = pa.Table.from_pylist(rows, schema=FEATURES_SCHEMA)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        payload = buffer.getvalue()

        try:
            await client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=object_name,
                Body=payload,
                ContentType="application/octet-stream",
            )
            logger.info(
                "features parquet uploaded",
                extra={
                    "bucket": settings.S3_BUCKET,
                    "object_name": object_name,
                    "rows": table.num_rows,
                },
            )
        except (BotoCoreError, ClientError):
            logger.error(
                "Failed to upload features parquet",
                extra={"bucket": settings.S3_BUCKET, "object_name": object_name},
                exc_info=True,
            )
            raise

    async def upload_file(self, object_name: str, file_path: str) -> None:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as file_obj:
            try:
                await client.put_object(
                    Bucket=settings.S3_BUCKET,
                    Key=object_name,
                    Body=file_obj,
                    ContentLength=file_size,
                    ContentType="application/octet-stream",
                )
                logger.info(
                    "features parquet file uploaded",
                    extra={
                        "bucket": settings.S3_BUCKET,
                        "object_name": object_name,
                        "bytes": file_size,
                    },
                )
            except (BotoCoreError, ClientError):
                logger.error(
                    "Failed to upload features parquet file",
                    extra={"bucket": settings.S3_BUCKET, "object_name": object_name},
                    exc_info=True,
                )
                raise

    async def _ensure_bucket_exists(self) -> None:
        client = self._client
        if client is None:
            raise RuntimeError("S3 client is not connected")

        try:
            await client.head_bucket(Bucket=settings.S3_BUCKET)
        except ClientError as error:
            status_code = error.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            if status_code != 404:
                raise
            await client.create_bucket(Bucket=settings.S3_BUCKET)


s3_parquet_client = S3ParquetClient()
