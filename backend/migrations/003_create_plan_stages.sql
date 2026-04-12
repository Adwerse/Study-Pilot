CREATE TABLE plan_stages (
	id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
	plan_id uuid NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
	week_number integer NOT NULL,
	title text NOT NULL,
	deliverable text NOT NULL,
	status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done')),
	order_index integer NOT NULL
);

CREATE INDEX ON plan_stages(plan_id);
