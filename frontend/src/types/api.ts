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

// Daily plan
export interface FocusBlock {
	title: string
	topic: string
	duration_minutes: number
	description: string
	priority: 1 | 2 | 3 | 4
}

export interface DailyPlan {
	blocks: FocusBlock[]
	daily_note: string
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
export type FocusSessionStatus = 'active' | 'completed' | 'cancelled'

export interface FocusSession {
	id: string
	user_id?: string
	stage_id?: string | null
	plan_id?: string | null
	plan_stage_id?: string | null
	status: FocusSessionStatus
	started_at: string
	ended_at?: string | null
	planned_duration_minutes?: number | null
	actual_duration_seconds?: number | null
	duration_minutes?: number | null
	topic?: string | null
	difficulty?: number | null
	notes?: string | null
	completed?: boolean
	created_at?: string | null
	updated_at?: string | null
}

export interface FocusHistoryParams {
	date?: string
	status?: FocusSessionStatus
	limit?: number
	offset?: number
}

export interface FocusHistoryResponse {
	items: FocusSession[]
	total: number
	limit: number
	offset: number
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

// Knowledge base / RAG
export type DocumentStatus = 'processing' | 'ready' | 'failed'
export type DocumentSourceType = 'upload' | 'telegram' | 'manual'

export interface KnowledgeDocument {
	id: string
	title: string
	filename: string
	content_type: string
	size_bytes: number
	status: DocumentStatus
	chunks_count: number
	error_message?: string | null
	created_at: string
	updated_at: string
}

export interface DocumentListParams {
	limit?: number
	offset?: number
	status?: DocumentStatus
	q?: string
}

export interface DocumentListResponse {
	items: KnowledgeDocument[]
	total: number
	limit: number
	offset: number
}

export interface DocumentUploadMetadata {
	title?: string
	source_type?: DocumentSourceType
	tags?: string[]
}

export interface DocumentUploadResponse {
	document_id: string
	status: DocumentStatus
	title: string
	filename: string
	content_type: string
	size_bytes: number
	chunks_count: number
}

export type RAGConfidence = 'low' | 'medium' | 'high'

export interface RAGSource {
	document_id: string
	document_title: string
	filename: string
	chunk_id: string
	chunk_index: number
	score: number
	page_number?: number | null
	snippet: string
}

export interface AskQuestionPayload {
	question: string
	document_ids?: string[]
	top_k?: number
	rerank_top_k?: number
}

export interface AskResponse {
	answer: string
	sources: RAGSource[]
	rewritten_query?: string | null
	confidence: RAGConfidence
}
