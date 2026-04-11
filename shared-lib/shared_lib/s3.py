from contextlib import AsyncExitStack
from io import BytesIO
import os
from typing import Any

from aiobotocore.session import get_session
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger


class S3ParquetClient:
    def __init__(
        self,
        *,
        endpoint_url: str,
        region_name: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        use_ssl: bool = False,
        parquet_schema: Any | None = None,
    ) -> None:
        self._session = get_session()
        self._exit_stack: AsyncExitStack | None = None
        self._client: Any | None = None
        self._endpoint_url = endpoint_url
        self._region_name = region_name
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._bucket = bucket
        self._use_ssl = use_ssl
        self._parquet_schema = parquet_schema

    async def connect(self) -> Any | None:
        if self._client is not None:
            return self._client

        self._exit_stack = AsyncExitStack()
        try:
            self._client = await self._exit_stack.enter_async_context(
                self._session.create_client(
                    "s3",
                    endpoint_url=self._endpoint_url,
                    region_name=self._region_name,
                    aws_access_key_id=self._access_key_id,
                    aws_secret_access_key=self._secret_access_key,
                    use_ssl=self._use_ssl,
                )
            )
            await self._ensure_bucket_exists()
            return self._client
        except (BotoCoreError, ClientError):
            logger.error(
                "Unable to connect to S3",
                extra={
                    "s3_endpoint": self._endpoint_url,
                    "s3_bucket": self._bucket,
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
        if self._parquet_schema is None:
            raise RuntimeError("Parquet schema is not configured for S3ParquetClient")

        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.Table.from_pylist(rows, schema=self._parquet_schema)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        payload = buffer.getvalue()

        try:
            await client.put_object(
                Bucket=self._bucket,
                Key=object_name,
                Body=payload,
                ContentType="application/octet-stream",
            )
            logger.info(
                "features parquet uploaded",
                extra={
                    "bucket": self._bucket,
                    "object_name": object_name,
                    "rows": table.num_rows,
                },
            )
        except (BotoCoreError, ClientError):
            logger.error(
                "Failed to upload features parquet",
                extra={"bucket": self._bucket, "object_name": object_name},
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
                    Bucket=self._bucket,
                    Key=object_name,
                    Body=file_obj,
                    ContentLength=file_size,
                    ContentType="application/octet-stream",
                )
                logger.info(
                    "features parquet file uploaded",
                    extra={
                        "bucket": self._bucket,
                        "object_name": object_name,
                        "bytes": file_size,
                    },
                )
            except (BotoCoreError, ClientError):
                logger.error(
                    "Failed to upload features parquet file",
                    extra={"bucket": self._bucket, "object_name": object_name},
                    exc_info=True,
                )
                raise

    async def upload_bytes(self, object_name: str, payload: bytes) -> None:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        try:
            await client.put_object(
                Bucket=self._bucket,
                Key=object_name,
                Body=payload,
                ContentLength=len(payload),
                ContentType="application/octet-stream",
            )
            logger.info(
                "features parquet bytes uploaded",
                extra={
                    "bucket": self._bucket,
                    "object_name": object_name,
                    "bytes": len(payload),
                },
            )
        except (BotoCoreError, ClientError):
            logger.error(
                "Failed to upload features parquet bytes",
                extra={"bucket": self._bucket, "object_name": object_name},
                exc_info=True,
            )
            raise

    async def create_multipart_upload(self, object_name: str) -> str:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        response = await client.create_multipart_upload(
            Bucket=self._bucket,
            Key=object_name,
            ContentType="application/octet-stream",
        )
        upload_id = response.get("UploadId")
        if not upload_id:
            raise RuntimeError("S3 multipart upload_id is missing")
        return upload_id

    async def upload_part(
        self,
        object_name: str,
        upload_id: str,
        part_number: int,
        payload: bytes,
    ) -> str:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        response = await client.upload_part(
            Bucket=self._bucket,
            Key=object_name,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=payload,
            ContentLength=len(payload),
        )
        etag = response.get("ETag")
        if not etag:
            raise RuntimeError("S3 multipart upload part ETag is missing")
        return str(etag)

    async def complete_multipart_upload(
        self,
        object_name: str,
        upload_id: str,
        parts: list[dict[str, str | int]],
    ) -> None:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        await client.complete_multipart_upload(
            Bucket=self._bucket,
            Key=object_name,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )

    async def abort_multipart_upload(self, object_name: str, upload_id: str) -> None:
        client = await self.connect()
        if client is None:
            raise RuntimeError("S3 client is not connected")

        await client.abort_multipart_upload(
            Bucket=self._bucket,
            Key=object_name,
            UploadId=upload_id,
        )

    async def _ensure_bucket_exists(self) -> None:
        client = self._client
        if client is None:
            raise RuntimeError("S3 client is not connected")

        try:
            await client.head_bucket(Bucket=self._bucket)
        except ClientError as error:
            status_code = error.response.get("ResponseMetadata", {}).get(
                "HTTPStatusCode"
            )
            if status_code != 404:
                raise
            await client.create_bucket(Bucket=self._bucket)
