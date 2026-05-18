ALTER TABLE users
	ADD COLUMN IF NOT EXISTS timezone text NOT NULL DEFAULT 'UTC',
	ADD COLUMN IF NOT EXISTS notifications_enabled boolean NOT NULL DEFAULT true,
	ADD COLUMN IF NOT EXISTS weekly_digest_enabled boolean NOT NULL DEFAULT true;

CREATE TABLE IF NOT EXISTS weekly_digest_deliveries (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	telegram_id bigint NOT NULL,
	week_start timestamptz NOT NULL,
	week_end timestamptz NOT NULL,
	timezone text NOT NULL DEFAULT 'UTC',
	status varchar(20) NOT NULL DEFAULT 'pending',
	message_text text,
	telegram_message_id bigint,
	error_message text,
	sent_at timestamptz,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT ck_weekly_digest_deliveries_status CHECK (
		status IN ('pending', 'sent', 'failed', 'skipped')
	),
	CONSTRAINT ux_weekly_digest_deliveries_user_week UNIQUE (
		user_id,
		week_start,
		week_end
	)
);

CREATE INDEX IF NOT EXISTS ix_weekly_digest_deliveries_user_created
	ON weekly_digest_deliveries(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_weekly_digest_deliveries_status_created
	ON weekly_digest_deliveries(status, created_at DESC);
