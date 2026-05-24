CREATE TABLE IF NOT EXISTS focus_log (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	stage_id uuid REFERENCES plan_stages(id) ON DELETE SET NULL,
	started_at timestamptz NOT NULL,
	ended_at timestamptz,
	duration_minutes integer,
	topic text NOT NULL,
	difficulty integer CHECK (difficulty BETWEEN 1 AND 5),
	completed boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS focus_log_user_id_started_at_idx
	ON focus_log(user_id, started_at);
