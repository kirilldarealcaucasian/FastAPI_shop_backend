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
    actor_type SMALLINT,
    user_id INT,
    session_id UUID,
    user_idx INT,

    UNIQUE (actor_type, user_id, session_id)
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'events'
          AND table_name = 'interaction_events'
          AND column_name = 'user_id'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'events'
          AND table_name = 'interaction_events'
          AND column_name = 'actor_id'
    ) THEN
        ALTER TABLE events.interaction_events RENAME COLUMN user_id TO actor_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'events'
          AND table_name = 'interaction_events'
          AND column_name = 'session_id'
    ) THEN
        ALTER TABLE events.interaction_events DROP COLUMN session_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'events'
          AND table_name = 'user_index_map'
    ) THEN
        ALTER TABLE events.user_index_map ADD COLUMN IF NOT EXISTS actor_type SMALLINT;
        ALTER TABLE events.user_index_map ADD COLUMN IF NOT EXISTS user_id INT;
        ALTER TABLE events.user_index_map ADD COLUMN IF NOT EXISTS session_id UUID;
        ALTER TABLE events.user_index_map ADD COLUMN IF NOT EXISTS user_idx INT;

        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'events'
              AND table_name = 'user_index_map'
              AND column_name = 'actor_id'
        ) THEN
            UPDATE events.user_index_map
            SET actor_type = COALESCE(actor_type, 1),
                user_id = COALESCE(user_id, actor_id::INT)
            WHERE actor_id IS NOT NULL;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'events'
              AND table_name = 'user_index_map'
              AND column_name = 'user_index'
        ) THEN
            UPDATE events.user_index_map
            SET user_idx = COALESCE(user_idx, user_index::INT)
            WHERE user_idx IS NULL;
        END IF;
    END IF;
END $$;

DROP INDEX IF EXISTS events.ix_user_index_map_actor_id;
DROP INDEX IF EXISTS events.ux_user_index_map_actor_user_session;

DO $$
DECLARE
    c_name TEXT;
BEGIN
    FOR c_name IN
        SELECT DISTINCT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_schema = kcu.constraint_schema
            AND tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'events'
          AND tc.table_name = 'user_index_map'
          AND kcu.column_name IN ('actor_id', 'user_index')
    LOOP
        EXECUTE format('ALTER TABLE events.user_index_map DROP CONSTRAINT %I', c_name);
    END LOOP;
END $$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'events'
          AND table_name = 'user_index_map'
          AND column_name = 'actor_id'
    ) THEN
        ALTER TABLE events.user_index_map DROP COLUMN actor_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'events'
          AND table_name = 'user_index_map'
          AND column_name = 'user_index'
    ) THEN
        ALTER TABLE events.user_index_map DROP COLUMN user_index;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS events.item_index_map (
    item_index BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS ix_interaction_events_event_timestamp
    ON events.interaction_events (event_timestamp);
CREATE INDEX IF NOT EXISTS ix_interaction_events_actor_item_date
    ON events.interaction_events (actor_id, item_id, event_timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS ux_user_index_map_actor_user_session
    ON events.user_index_map (actor_type, user_id, session_id);
CREATE INDEX IF NOT EXISTS ix_item_index_map_item_id
    ON events.item_index_map (item_id);

COMMIT;
