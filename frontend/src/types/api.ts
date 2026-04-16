// Error envelope
export interface ApiError {
	detail: string
	status: number
}

// User
export interface User {
	id: string
	telegram_id: number
	username?: string
	first_name?: string
	goal?: string
	deadline?: string
	level?: 'beginner' | 'intermediate' | 'advanced'
	weekly_hours?: number
}

// Plan stage
export interface PlanStage {
	id: string
	plan_id: string
	week_number: number
	title: string
	deliverable: string
	status: 'pending' | 'in_progress' | 'done'
	order_index: number
}

// Plan
export interface Plan {
	id: string
	user_id: string
	title: string
	status: 'active' | 'paused' | 'completed'
	generated_at: string
	adapted_at?: string
	stages?: PlanStage[]
}

// Focus session
export interface FocusSession {
	id: string
	user_id: string
	stage_id?: string
	started_at: string
	ended_at?: string
	duration_minutes?: number
	topic: string
	difficulty?: number
	completed: boolean
}

// Analytics
export interface DailyMetrics {
	date: string
	sessions_count: number
	total_minutes: number
	completion_rate: number
	streak_days: number
	best_hour?: number
}

// RAG answer
export interface AskResponse {
	answer: string
	sources: Array<{ title: string; chunk: string }>
}

// Document
export interface Document {
	id: string
	title: string
	created_at: string
	tags?: string[]
}
