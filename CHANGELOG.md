# Changelog

## 2026-05-02

### Added

- Added shared recommendation package in `shared-lib`:
  - `BookEventAction` enum with server-side event weights.
  - `BookEventMessage` shared between `events-collector` and `events-saver`.
  - `UserSessionLinkMessage` shared between `auth` and `events-saver`.
- Added Kafka publishing to `auth` so successful registration can publish a user-session link message to `auth_events`.
- Added `events-saver/event_saver/processor.py` to keep Kafka parsing separate from database processing.
- Added `events-saver/event_saver/sql.py` for reusable SQL operations.
- Added marketplace backend helper `prolong_events_session_cookie()` for refreshing the events session cookie.
- Added more `events-saver` logs around startup, Kafka batches, parse results, malformed messages, database writes, and offset commits.

### Changed

- Changed event collection request shape:
  - Request body now contains only event data: `book_id`, `action`, and `ts`.
  - JWT is read from the `Authorization` header.
  - Events session id is read from the `events_session_id` cookie.
  - Numeric event weight is no longer accepted from clients; it is derived server-side from the action.
- Moved event request models out of `events-collector/cmd.py` into `events-collector/models.py`.
- Changed `events-collector` to publish shared `BookEventMessage` objects, including `session_expiration_time` supplied by the cookie issuer.
- Changed marketplace frontend event names to canonical actions: `view`, `long_view`, `cart`, and `purchase`.
- Changed marketplace frontend event sending to use cookies via `credentials: "include"` and to stop sending mock user/session data.
- Changed marketplace backend to issue/prolong both the events session id cookie and its matching frontend-readable session expiration cookie.
- Changed marketplace frontend to forward `events_session_expiration_time` to `events-collector` through `X-Events-Session-Expiration-Time`.
- Changed marketplace backend book routes to refresh the `events_session_id` cookie on book list/detail requests.
- Changed `events-saver` to consume two Kafka topics:
  - `book_events` for `BookEventMessage`.
  - `auth_events` for `UserSessionLinkMessage`.
- Changed `events-saver` persistence so `user_index_map.session_expiration_time` is stored and refreshed from incoming event/link messages.
- Changed `events-saver` to pass around `BookEventMessage` and `UserSessionLinkMessage` objects instead of intermediate row dicts.
- Changed `events-saver` database code so `db.py` only owns connection, schema validation, and migration execution.
- Changed `events-saver` migration to focus on table/index creation for the current schema.
- Changed `user_index_map` to remove `actor_type`, key by `session_id`, and store optional `user_id` plus `session_expiration_time`.
- Updated Docker Compose environment for auth Kafka publishing and separate event saver topics.
- Updated auth and events service READMEs to document the event/session link flow.

### Removed

- Removed client-provided `weight`, `session_id`, `user_id`, and `jwt_token` from the collector request body.
- Removed old event aliases such as `description_open`, `description_long_read`, `add_to_cart`, and `buy` from the active frontend event flow.
- Removed row-conversion logic from `events-saver` database persistence.
- Removed legacy `actor_type` mapping logic from `events-saver`.
