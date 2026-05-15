ALTER TABLE plan_stages
	ADD COLUMN IF NOT EXISTS completed_at timestamptz;

ALTER TABLE weekly_reviews
	ADD COLUMN IF NOT EXISTS roadmap_status text NOT NULL DEFAULT 'insufficient_data';

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'ck_weekly_reviews_roadmap_status'
	) THEN
		ALTER TABLE weekly_reviews
			ADD CONSTRAINT ck_weekly_reviews_roadmap_status CHECK (
				roadmap_status IN ('on_track', 'behind', 'ahead', 'insufficient_data')
			);
	END IF;
END $$;
