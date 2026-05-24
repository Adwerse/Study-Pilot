CREATE TABLE IF NOT EXISTS plans (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
	title text NOT NULL,
	status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
	generated_at timestamptz NOT NULL DEFAULT now(),
	adapted_at timestamptz
);

CREATE INDEX IF NOT EXISTS plans_user_id_idx ON plans(user_id);
