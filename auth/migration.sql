BEGIN;

CREATE SCHEMA IF NOT EXISTS auth;

DROP TABLE IF EXISTS public.users;

CREATE TABLE IF NOT EXISTS auth.users (
    id BIGSERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role_name TEXT NOT NULL DEFAULT 'user',
    date_of_birth DATE NULL,
    CONSTRAINT ck_users_role_name CHECK (role_name IN ('user', 'manager', 'admin'))
);

CREATE INDEX IF NOT EXISTS ix_users_email ON auth.users (email);

COMMIT;
