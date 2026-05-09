# event-saver

Standalone worker service that consumes recommendation messages from Kafka.
Book interaction events are persisted to `interaction_events`; login/session link
messages update `user_index_map`.

## Environment

- `KAFKA_BOOTSTRAP_SERVERS` (default: `localhost:9092`)
- `KAFKA_BOOK_EVENTS_TOPIC` (default: `book_events`)
- `KAFKA_AUTH_EVENTS_TOPIC` (default: `auth_events`)
- `KAFKA_GROUP_ID` (default: `event-saver`)
- `KAFKA_AUTO_OFFSET_RESET` (default: `earliest`)
- `KAFKA_BATCH_SIZE` (default: `100`)
- `DB_URL` (optional full Postgres DSN, e.g. `postgresql://user:pass@host:5432/db`)
- `DB_USER`, `DB_PASSWORD`, `DB_SERVER`, `DB_PORT`, `DB_NAME`, `DB_SCHEMA`

If `DB_URL` is not provided, URL is built from DB_* vars.

## Consumed messages

The worker consumes shared recommendation messages:

- `BookEventMessage` from `KAFKA_BOOK_EVENTS_TOPIC`: saved to `interaction_events`
  and upserts its `session_id` into `user_index_map`.
- `UserSessionLinkMessage` from `KAFKA_AUTH_EVENTS_TOPIC`: updates
  `user_index_map.user_id` for the matching `session_id` when a user registers.

If required message fields are invalid, the message is skipped as malformed.

## Run locally

```bash
cd event-saver
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m event_saver.main
```
