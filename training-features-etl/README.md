# training-features-etl

Daily ETL service that reads `interaction_events` from Postgres, aggregates per subject/item/day,
serializes to Parquet, and uploads to S3/MinIO.

Output schema:

- `subject_key` string (`u:<user_id>` or `s:<session_id>`)
- `item_id` int64
- `view_cnt` int32
- `long_view_cnt` int32
- `cart_cnt` int32
- `purchase_cnt` int32
- `weight` float32
- `first_event_ts` timestamp
- `last_event_ts` timestamp
- `event_date` date

## Environment

- `DB_URL` optional DSN (`postgresql://...`)
- `DB_USER`, `DB_PASSWORD`, `DB_SERVER`, `DB_PORT`, `DB_NAME`, `DB_SCHEMA`
- `S3_ENDPOINT_URL` default `http://localhost:9000`
- `S3_ACCESS_KEY` default `minioadmin`
- `S3_SECRET_KEY` default `minioadmin`
- `S3_BUCKET` default `events`
- `S3_REGION` default `us-east-1`
- `S3_SECURE` default `false`
- `S3_OBJECT_PREFIX` default `training_features`
- `ETL_RUN_AT_UTC` default `00:15` (HH:MM)
- `ETL_RUN_ON_STARTUP` default `true`
- `ETL_LOOKBACK_DAYS` default `1` (usually yesterday)
- `ETL_BATCH_SIZE` default `10000`

## Run

```bash
cd training-features-etl
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m training_features_etl.main
```
