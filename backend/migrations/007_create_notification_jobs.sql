CREATE TABLE IF NOT EXISTS notification_jobs (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	focus_session_id uuid NOT NULL REFERENCES focus_log(id) ON DELETE CASCADE,
	telegram_id bigint NOT NULL,
	type varchar(20) NOT NULL,
	status varchar(20) NOT NULL DEFAULT 'pending',
	scheduled_at timestamptz NOT NULL,
	sent_at timestamptz,
	error_message text,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now(),
	CONSTRAINT ck_notification_jobs_type CHECK (type IN ('focus_end', 'break_end')),
	CONSTRAINT ck_notification_jobs_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS ix_notification_jobs_pending_scheduled_at
	ON notification_jobs(scheduled_at)
	WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS ix_notification_jobs_focus_session
	ON notification_jobs(focus_session_id);
