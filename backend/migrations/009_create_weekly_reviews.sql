ALTER TABLE plan_stages
	ADD COLUMN IF NOT EXISTS start_date date,
	ADD COLUMN IF NOT EXISTS end_date date;

UPDATE plan_stages
SET
	start_date = (plans.generated_at AT TIME ZONE 'UTC')::date
		+ ((GREATEST(plan_stages.week_number, 1) - 1) * 7),
	end_date = (plans.generated_at AT TIME ZONE 'UTC')::date
		+ ((GREATEST(plan_stages.week_number, 1) - 1) * 7)
		+ 6
FROM plans
WHERE plan_stages.plan_id = plans.id
	AND (plan_stages.start_date IS NULL OR plan_stages.end_date IS NULL);

CREATE TABLE IF NOT EXISTS weekly_reviews (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	plan_id uuid NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
	period_start timestamptz NOT NULL,
	period_end timestamptz NOT NULL,
	timezone text NOT NULL DEFAULT 'UTC',
	status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'applied', 'dismissed')),
	summary text NOT NULL,
	insights jsonb NOT NULL DEFAULT '[]'::jsonb,
	risks jsonb NOT NULL DEFAULT '[]'::jsonb,
	recommendations jsonb NOT NULL DEFAULT '[]'::jsonb,
	metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
	proposed_changes jsonb NOT NULL DEFAULT '[]'::jsonb,
	applied_at timestamptz,
	created_at timestamptz NOT NULL DEFAULT now(),
	updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_weekly_reviews_user_created
	ON weekly_reviews(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_weekly_reviews_user_plan_created
	ON weekly_reviews(user_id, plan_id, created_at DESC);
