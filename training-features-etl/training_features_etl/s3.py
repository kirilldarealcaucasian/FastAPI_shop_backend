import pyarrow as pa
from shared_lib.s3 import S3ParquetClient

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


s3_parquet_client = S3ParquetClient(
    endpoint_url=settings.S3_ENDPOINT_URL,
    region_name=settings.S3_REGION,
    access_key_id=settings.S3_ACCESS_KEY,
    secret_access_key=settings.S3_SECRET_KEY,
    bucket=settings.S3_BUCKET,
    use_ssl=settings.S3_SECURE,
    parquet_schema=FEATURES_SCHEMA,
)
