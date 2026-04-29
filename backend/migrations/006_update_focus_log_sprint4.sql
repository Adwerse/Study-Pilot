ALTER TABLE focus_log
	ADD COLUMN IF NOT EXISTS plan_id uuid REFERENCES plans(id) ON DELETE SET NULL,
	ADD COLUMN IF NOT EXISTS plan_stage_id uuid REFERENCES plan_stages(id) ON DELETE SET NULL,
	ADD COLUMN IF NOT EXISTS status varchar(20),
	ADD COLUMN IF NOT EXISTS planned_duration_minutes integer,
	ADD COLUMN IF NOT EXISTS actual_duration_seconds integer,
	ADD COLUMN IF NOT EXISTS notes text,
	ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
	ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
	IF EXISTS (
		SELECT 1
		FROM information_schema.columns
		WHERE table_name = 'focus_log'
			AND column_name = 'stage_id'
	) THEN
		UPDATE focus_log
		SET plan_stage_id = stage_id
		WHERE plan_stage_id IS NULL
			AND stage_id IS NOT NULL;
	END IF;
END $$;

UPDATE focus_log
SET plan_id = plan_stages.plan_id
FROM plan_stages
WHERE focus_log.plan_id IS NULL
	AND focus_log.plan_stage_id = plan_stages.id;

UPDATE focus_log
SET status = CASE
	WHEN COALESCE(completed, false) = true THEN 'completed'
	WHEN ended_at IS NOT NULL THEN 'completed'
	ELSE 'active'
END
WHERE status IS NULL;

UPDATE focus_log
SET actual_duration_seconds = GREATEST(0, FLOOR(EXTRACT(EPOCH FROM ended_at - started_at))::integer)
WHERE actual_duration_seconds IS NULL
	AND ended_at IS NOT NULL;

UPDATE focus_log
SET actual_duration_seconds = GREATEST(0, duration_minutes * 60)
WHERE actual_duration_seconds IS NULL
	AND duration_minutes IS NOT NULL;

ALTER TABLE focus_log
	ALTER COLUMN status SET DEFAULT 'active',
	ALTER COLUMN status SET NOT NULL,
	ALTER COLUMN topic DROP NOT NULL;

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_focus_log_status'
	) THEN
		ALTER TABLE focus_log
			ADD CONSTRAINT ck_focus_log_status CHECK (status IN ('active', 'completed', 'cancelled'));
	END IF;

	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_focus_log_difficulty'
	) THEN
		ALTER TABLE focus_log
			ADD CONSTRAINT ck_focus_log_difficulty CHECK (difficulty IS NULL OR difficulty BETWEEN 1 AND 5);
	END IF;

	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_focus_log_planned_duration'
	) THEN
		ALTER TABLE focus_log
			ADD CONSTRAINT ck_focus_log_planned_duration CHECK (
				planned_duration_minutes IS NULL
				OR (planned_duration_minutes > 0 AND planned_duration_minutes <= 180)
			);
	END IF;

	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_focus_log_actual_duration'
	) THEN
		ALTER TABLE focus_log
			ADD CONSTRAINT ck_focus_log_actual_duration CHECK (
				actual_duration_seconds IS NULL
				OR actual_duration_seconds >= 0
			);
	END IF;

	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_focus_log_topic_length'
	) THEN
		ALTER TABLE focus_log
			ADD CONSTRAINT ck_focus_log_topic_length CHECK (topic IS NULL OR char_length(topic) <= 255);
	END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_focus_log_user_started_at
	ON focus_log(user_id, started_at);

CREATE UNIQUE INDEX IF NOT EXISTS ux_focus_log_one_active_per_user
	ON focus_log(user_id)
	WHERE status = 'active';
