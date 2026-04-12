# events_collector

Minimal service that receives user-book interaction events, stores them in Redis,
and publishes them to Kafka.

If request payload contains `jwt_token`, service decodes it and, when claim `user_id` exists,
adds `user_id` to the produced Kafka message.

`session_id` is resolved from request payload first; when it is absent there, the service
extracts it from cookie `events_session_id`.

Redis storage policy:
- Events are stored per user key (or per session when `user_id` is absent).
- Maximum 50 latest events are kept per key.
- Keys expire after 7 days.
