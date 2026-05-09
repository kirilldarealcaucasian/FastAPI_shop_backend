INSERT_SESSION_MAPPINGS = """
    INSERT INTO {schema}.user_index_map (session_id, session_expiration_time)
    SELECT t.session_id, t.session_expiration_time
    FROM UNNEST($1::UUID[], $2::TIMESTAMP[]) AS t(session_id, session_expiration_time)
    ON CONFLICT (session_id) DO UPDATE
    SET session_expiration_time = GREATEST(
        {schema}.user_index_map.session_expiration_time,
        EXCLUDED.session_expiration_time
    )
    WHERE {schema}.user_index_map.session_expiration_time < EXCLUDED.session_expiration_time
"""

INSERT_ITEM_MAPPINGS = """
    INSERT INTO {schema}.item_index_map (item_id)
    SELECT item_id
    FROM UNNEST($1::BIGINT[]) AS t(item_id)
    ON CONFLICT (item_id) DO NOTHING
"""

LINK_USER_SESSIONS = """
    INSERT INTO {schema}.user_index_map (user_id, session_id, session_expiration_time)
    SELECT t.user_id, t.session_id, t.session_expiration_time
    FROM UNNEST($1::INT[], $2::UUID[], $3::TIMESTAMP[]) AS t(user_id, session_id, session_expiration_time)
    ON CONFLICT (session_id) DO UPDATE
    SET user_id = EXCLUDED.user_id,
        session_expiration_time = EXCLUDED.session_expiration_time
    WHERE user_index_map.user_id IS DISTINCT FROM EXCLUDED.user_id
       OR user_index_map.session_expiration_time IS DISTINCT FROM EXCLUDED.session_expiration_time
"""

__all__ = (
    "INSERT_SESSION_MAPPINGS",
    "INSERT_ITEM_MAPPINGS",
    "LINK_USER_SESSIONS",
)
