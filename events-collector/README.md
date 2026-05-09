# events_collector

Minimal service that receives user-book interaction events, stores them in Redis,
and publishes them to Kafka.

If request contains `Authorization: Bearer <jwt>`, service decodes it and, when claim
`user_id` exists, adds `user_id` to the produced Kafka message.

Incoming `action` is the event action label. The collector derives the canonical
event name and numeric event weight server-side before storing and publishing it.

`session_id` is extracted from cookie `events_session_id`.

Redis storage policy:
- Events are stored per user key (or per session when `user_id` is absent).
- Maximum 50 latest events are kept per key.
- Keys expire after 7 days.
