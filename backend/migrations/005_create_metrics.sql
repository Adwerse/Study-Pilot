CREATE TABLE metrics (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	date date NOT NULL,
	sessions_count integer NOT NULL DEFAULT 0,
	total_minutes integer NOT NULL DEFAULT 0,
	completion_rate numeric(5,2) NOT NULL DEFAULT 0,
	streak_days integer NOT NULL DEFAULT 0,
	best_hour integer CHECK (best_hour BETWEEN 0 AND 23)
);

CREATE UNIQUE INDEX ON metrics(user_id, date);
