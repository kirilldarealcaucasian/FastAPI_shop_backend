from __future__ import annotations

from contextlib import AsyncExitStack
from io import BytesIO
from typing import Any

from aiobotocore.session import get_session
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq

from application.settings import settings


class MinioConnector:
    """Async connector for MinIO event storage in Parquet format."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
        secure: bool = False,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region = region
        self.secure = secure

        self._session = get_session()
        self._exit_stack: AsyncExitStack | None = None
        self._client: Any | None = None

    @property
    def client(self) -> Any | None:
        return self._client

    async def connect(self) -> Any | None:
        """Create or return active S3-compatible client."""
        if self._client is not None:
            return self._client

        self._exit_stack = AsyncExitStack()
        try:
            self._client = await self._exit_stack.enter_async_context(
                self._session.create_client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    use_ssl=self.secure,
                )
            )
            await self._ensure_bucket_exists()
            logger.info(
                "Connected to MinIO",
                extra={
                    "minio_endpoint": self.endpoint_url,
                    "minio_bucket": self.bucket_name,
                },
            )
            return self._client
        except (BotoCoreError, ClientError):
            logger.error(
                "Unable to connect to MinIO",
                extra={
                    "minio_endpoint": self.endpoint_url,
                    "minio_bucket": self.bucket_name,
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
            logger.info("Disconnected from MinIO")

    async def write_events_parquet(
        self,
        object_name: str,
        events: list[dict[str, Any]],
    ) -> None:
        """Serialize event records to parquet and upload to MinIO."""
        client = await self.connect()
        if client is None:
            raise RuntimeError("MinIO client is not connected")

        table = pa.Table.from_pylist(events)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        payload = buffer.getvalue()

        try:
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=payload,
                ContentType="application/octet-stream",
            )
            logger.info(
                "Events parquet uploaded",
                extra={
                    "minio_bucket": self.bucket_name,
                    "object_name": object_name,
                    "rows": table.num_rows,
                },
            )
        except (BotoCoreError, ClientError):
            logger.error(
                "Failed to upload events parquet",
                extra={"minio_bucket": self.bucket_name, "object_name": object_name},
                exc_info=True,
            )
            raise

    async def read_events_parquet(self, object_name: str) -> list[dict[str, Any]]:
        """Download parquet object from MinIO and return event records."""
        client = await self.connect()
        if client is None:
            raise RuntimeError("MinIO client is not connected")

        try:
            response = await client.get_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )
            async with response["Body"] as stream:
                raw_data = await stream.read()
            table = pq.read_table(BytesIO(raw_data))
            rows = table.to_pylist()
            logger.info(
                "Events parquet downloaded",
                extra={
                    "minio_bucket": self.bucket_name,
                    "object_name": object_name,
                    "rows": len(rows),
                },
            )
            return rows
        except (BotoCoreError, ClientError):
            logger.error(
                "Failed to read events parquet",
                extra={"minio_bucket": self.bucket_name, "object_name": object_name},
                exc_info=True,
            )
            raise

    async def _ensure_bucket_exists(self) -> None:
        client = self._client
        if client is None:
            raise RuntimeError("MinIO client is not connected")

        try:
            await client.head_bucket(Bucket=self.bucket_name)
        except ClientError as error:
            status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code != 404:
                raise
            await client.create_bucket(Bucket=self.bucket_name)
            logger.info(
                "Created MinIO bucket",
                extra={"minio_bucket": self.bucket_name},
            )


minio_client = MinioConnector(
    endpoint_url=settings.MINIO_ENDPOINT_URL,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    bucket_name=settings.MINIO_EVENTS_BUCKET,
    region=settings.MINIO_REGION,
    secure=settings.MINIO_SECURE,
)
