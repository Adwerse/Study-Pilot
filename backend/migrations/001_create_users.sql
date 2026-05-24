CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	telegram_id bigint UNIQUE NOT NULL,
	username text,
	goal text,
	deadline date,
	level text CHECK (level IN ('beginner', 'intermediate', 'advanced')),
	weekly_hours integer,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS users_telegram_id_idx ON users(telegram_id);
