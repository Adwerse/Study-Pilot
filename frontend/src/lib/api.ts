import axios, { AxiosError, AxiosProgressEvent } from 'axios'
import type {
  AskQuestionPayload,
  AskResponse,
  ApiError,
  DailyMetrics,
  DailyPlan,
  DocumentListParams,
  DocumentListResponse,
  DocumentUploadMetadata,
  DocumentUploadResponse,
  FocusHistoryParams,
  FocusHistoryResponse,
  FocusSession,
  Plan,
  User,
} from '../types/api'
import { getInitData, tg } from './telegram'

type CreatePlanPayload = {
  goal: string
  level?: 'beginner' | 'intermediate' | 'advanced'
  weekly_hours?: number
  deadline?: string
}

type UploadDocumentOptions = {
  signal?: AbortSignal
  onUploadProgress?: (progressEvent: AxiosProgressEvent) => void
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

function isApiError(error: unknown): error is ApiError {
  if (typeof error !== 'object' || error === null) {
    return false
  }

  const maybeApiError = error as Partial<ApiError>
  return typeof maybeApiError.detail === 'string' && typeof maybeApiError.status === 'number'
}

export function normalizeApiError(error: unknown): ApiError {
  if (isApiError(error)) {
    return error
  }

  const axiosError = error as AxiosError<{ detail?: string | string[] }>
  const status = axiosError?.response?.status ?? 500
  const rawDetail = axiosError?.response?.data?.detail

  if (Array.isArray(rawDetail)) {
    return {
      detail: rawDetail.join(', '),
      status,
    }
  }

  if (typeof rawDetail === 'string' && rawDetail.trim().length > 0) {
    return {
      detail: rawDetail,
      status,
    }
  }

  if (typeof axiosError?.message === 'string' && axiosError.message.trim().length > 0) {
    return {
      detail: axiosError.message,
      status,
    }
  }

  return {
    detail: 'Unknown API error',
    status,
  }
}

api.interceptors.request.use((config) => {
  const initData = getInitData()

  if (initData) {
    config.headers.Authorization = `tma ${initData}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalizedError = normalizeApiError(error)

    if (normalizedError.status === 401) {
      tg.close()
    }

    if (import.meta.env.DEV) {
      console.error('[api]', normalizedError)
    }

    return Promise.reject(normalizedError)
  },
)

export const apiClient = {
  // Users
  getMe: (signal?: AbortSignal) => api.get<User>('/api/v1/users/me', { signal }),
  updateMe: (data: Partial<User>, signal?: AbortSignal) => api.put<User>('/api/v1/users/me', data, { signal }),

  // Plans
  createPlan: (goal: string, payload?: Partial<CreatePlanPayload>, signal?: AbortSignal) =>
    api.post<Plan>('/api/v1/plans/', { ...payload, goal }, { signal }),
  getCurrentPlan: (signal?: AbortSignal) => api.get<Plan | null>('/api/v1/plans/current', { signal }),
  getToday: (signal?: AbortSignal) => api.get<DailyPlan>('/api/v1/plans/current/today', { signal }),
  recalculatePlan: (planId: string, signal?: AbortSignal) =>
    api.post<Plan>(`/api/v1/plans/${planId}/recalculate`, undefined, { signal }),

  // Focus
  startFocus: (topic: string, stageId?: string, signal?: AbortSignal) =>
    api.post<FocusSession>('/api/v1/focus/start', { topic, stage_id: stageId }, { signal }),
  endFocus: (sessionId: string, difficulty: number, signal?: AbortSignal) =>
    api.post<FocusSession>('/api/v1/focus/end', { session_id: sessionId, difficulty }, { signal }),
  getActiveSession: (signal?: AbortSignal) => api.get<FocusSession | null>('/api/v1/focus/active', { signal }),
  getFocusHistory: (params: FocusHistoryParams = {}, signal?: AbortSignal) =>
    api.get<FocusHistoryResponse>('/api/v1/focus/history', { params, signal }),

  // Knowledge base / RAG
  uploadDocument: (
    file: File,
    metadata: DocumentUploadMetadata = {},
    options: UploadDocumentOptions = {},
  ) => {
    const form = new FormData()
    form.append('file', file)

    if (metadata.title) {
      form.append('title', metadata.title)
    }

    if (metadata.source_type) {
      form.append('source_type', metadata.source_type)
    }

    if (metadata.tags?.length) {
      form.append('tags', metadata.tags.join(','))
    }

    return api.post<DocumentUploadResponse>('/api/v1/documents/upload', form, {
      signal: options.signal,
      onUploadProgress: options.onUploadProgress,
    })
  },
  getDocuments: (params: DocumentListParams = {}, signal?: AbortSignal) =>
    api.get<DocumentListResponse>('/api/v1/documents', { params, signal }),
  deleteDocument: (documentId: string, signal?: AbortSignal) =>
    api.delete<void>(`/api/v1/documents/${documentId}`, { signal }),
  askQuestion: (payload: AskQuestionPayload, signal?: AbortSignal) => api.post<AskResponse>('/api/v1/ask', payload, { signal }),
  ask: (question: string, signal?: AbortSignal) => api.post<AskResponse>('/api/v1/ask', { question }, { signal }),

  // Analytics
  getDailyMetrics: (signal?: AbortSignal) => api.get<DailyMetrics>('/api/v1/analytics/today', { signal }),
  getWeeklyMetrics: (signal?: AbortSignal) => api.get<DailyMetrics[]>('/api/v1/analytics/week', { signal }),
  getStreak: (signal?: AbortSignal) => api.get<{ streak_days: number }>('/api/v1/analytics/streak', { signal }),
}

export default api
