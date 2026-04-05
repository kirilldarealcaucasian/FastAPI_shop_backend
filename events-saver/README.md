# event-saver

Standalone worker service that consumes book interaction events from Kafka and persists them to Postgres table `interaction_events`.

## Environment

- `KAFKA_BOOTSTRAP_SERVERS` (default: `localhost:9092`)
- `KAFKA_TOPIC` (default: `book_events`)
- `KAFKA_GROUP_ID` (default: `event-saver`)
- `KAFKA_AUTO_OFFSET_RESET` (default: `earliest`)
- `KAFKA_BATCH_SIZE` (default: `100`)
- `DB_URL` (optional full Postgres DSN, e.g. `postgresql://user:pass@host:5432/db`)
- `DB_USER`, `DB_PASSWORD`, `DB_SERVER`, `DB_PORT`, `DB_NAME`, `DB_SCHEMA`

If `DB_URL` is not provided, URL is built from DB_* vars.

## Run locally

```bash
cd event-saver
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m event_saver.main
```
