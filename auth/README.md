# auth

Authentication service for registration, login, JWT issuance, and user management.

On successful registration, if the request contains cookie `events_session_id`,
the service publishes a `UserSessionLinkMessage` to Kafka topic `auth_events`.
`events-saver` consumes this message and updates `events.user_index_map` so the
anonymous events session is linked to the newly registered user.
