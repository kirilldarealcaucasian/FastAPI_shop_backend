-- Event-saver bootstrap migration.
-- The service owns creation of interaction_events.

BEGIN;

CREATE SCHEMA IF NOT EXISTS events;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'interaction_event_type'
          AND n.nspname = 'events'
    ) THEN
        CREATE TYPE events.interaction_event_type AS ENUM (
            'view',
            'long_view',
            'cart',
            'purchase'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS events.interaction_events (
    id BIGSERIAL PRIMARY KEY,
    actor_id BIGINT NULL,
    item_id BIGINT NOT NULL,
    event_type events.interaction_event_type NOT NULL,
    event_weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    event_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events.user_index_map (
    user_id INT,
    session_id UUID,
    session_expiration_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    user_idx INT,

    UNIQUE (session_id)
);

CREATE TABLE IF NOT EXISTS events.item_index_map (
    item_index BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS ix_interaction_events_event_timestamp
    ON events.interaction_events (event_timestamp);
CREATE INDEX IF NOT EXISTS ix_interaction_events_actor_item_date
    ON events.interaction_events (actor_id, item_id, event_timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS ux_user_index_map_session_id
    ON events.user_index_map (session_id);
CREATE INDEX IF NOT EXISTS ix_item_index_map_item_id
    ON events.item_index_map (item_id);

COMMIT;
