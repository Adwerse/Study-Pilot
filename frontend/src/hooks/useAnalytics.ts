import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type {
	AnalyticsDataQuality,
	AnalyticsMetrics,
	AnalyticsPeriod,
	AnalyticsPeriodType,
	AnalyticsReportResponse,
	ApiError,
	DailyBreakdownItem,
	WeeklyAnalyticsReportResponse,
} from '../types/api'

export interface UseDailyAnalyticsParams {
	date?: string
	timezone?: string
	enabled?: boolean
}

export interface UseWeeklyAnalyticsParams {
	weekStart?: string
	timezone?: string
	enabled?: boolean
}

export interface UseAnalyticsReportReturn<TReport> {
	data: TReport | null
	loading: boolean
	error: ApiError | null
	refetch: () => void
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null
}

function isAnalyticsPeriodType(value: unknown): value is AnalyticsPeriodType {
	return value === 'daily' || value === 'weekly'
}

function isAnalyticsDataQuality(value: unknown): value is AnalyticsDataQuality {
	return value === 'low' || value === 'medium' || value === 'high'
}

function isNullableNumber(value: unknown): value is number | null {
	return value === null || typeof value === 'number'
}

function isStringArray(value: unknown): value is string[] {
	return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isAnalyticsPeriod(value: unknown, expectedType?: AnalyticsPeriodType): value is AnalyticsPeriod {
	if (!isRecord(value)) {
		return false
	}

	return (
		isAnalyticsPeriodType(value.type) &&
		(expectedType === undefined || value.type === expectedType) &&
		typeof value.start === 'string' &&
		typeof value.end === 'string' &&
		typeof value.timezone === 'string'
	)
}

function isAnalyticsMetrics(value: unknown): value is AnalyticsMetrics {
	if (!isRecord(value)) {
		return false
	}

	return (
		typeof value.total_focus_minutes === 'number' &&
		typeof value.sessions_count === 'number' &&
		typeof value.cancelled_sessions_count === 'number' &&
		isNullableNumber(value.completion_rate) &&
		isNullableNumber(value.average_session_minutes) &&
		typeof value.streak_days === 'number' &&
		isStringArray(value.best_focus_hours) &&
		Array.isArray(value.most_focused_topics)
	)
}

function isDailyBreakdownItem(value: unknown): value is DailyBreakdownItem {
	if (!isRecord(value)) {
		return false
	}

	return (
		typeof value.date === 'string' &&
		typeof value.focus_minutes === 'number' &&
		typeof value.sessions_count === 'number' &&
		isNullableNumber(value.completion_rate)
	)
}

function isAnalyticsReport(value: unknown, expectedType: AnalyticsPeriodType): value is AnalyticsReportResponse {
	if (!isRecord(value)) {
		return false
	}

	return (
		isAnalyticsPeriod(value.period, expectedType) &&
		isAnalyticsMetrics(value.metrics) &&
		typeof value.summary === 'string' &&
		Array.isArray(value.recommendations) &&
		value.recommendations.every((item) => typeof item === 'string') &&
		isAnalyticsDataQuality(value.data_quality)
	)
}

function isWeeklyAnalyticsReport(value: unknown): value is WeeklyAnalyticsReportResponse {
	const reportWithBreakdown = value as { daily_breakdown?: unknown }

	return (
		isAnalyticsReport(value, 'weekly') &&
		Array.isArray(reportWithBreakdown.daily_breakdown) &&
		reportWithBreakdown.daily_breakdown.every(isDailyBreakdownItem)
	)
}

function invalidAnalyticsResponse(): ApiError {
	return {
		detail: 'Invalid analytics response',
		status: 500,
	}
}

export function useDailyAnalytics({
	date,
	timezone,
	enabled = true,
}: UseDailyAnalyticsParams = {}): UseAnalyticsReportReturn<AnalyticsReportResponse> {
	const [data, setData] = useState<AnalyticsReportResponse | null>(null)
	const [loading, setLoading] = useState(enabled)
	const [error, setError] = useState<ApiError | null>(null)
	const [refreshIndex, setRefreshIndex] = useState(0)
	const params = useMemo(() => ({ date, timezone }), [date, timezone])

	const refetch = useCallback(() => {
		setRefreshIndex((previous) => previous + 1)
	}, [])

	useEffect(() => {
		if (!enabled) {
			setLoading(false)
			return undefined
		}

		const controller = new AbortController()

		setData(null)
		setLoading(true)
		setError(null)

		apiClient
			.getDailyAnalytics(params, controller.signal)
			.then((response) => {
				if (controller.signal.aborted) {
					return
				}

				if (!isAnalyticsReport(response.data, 'daily')) {
					throw invalidAnalyticsResponse()
				}

				setData(response.data)
				setLoading(false)
			})
			.catch((analyticsError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(analyticsError))
				setData(null)
				setLoading(false)
			})

		return () => {
			controller.abort()
		}
	}, [enabled, params, refreshIndex])

	return {
		data,
		loading,
		error,
		refetch,
	}
}

export function useWeeklyAnalytics({
	weekStart,
	timezone,
	enabled = true,
}: UseWeeklyAnalyticsParams = {}): UseAnalyticsReportReturn<WeeklyAnalyticsReportResponse> {
	const [data, setData] = useState<WeeklyAnalyticsReportResponse | null>(null)
	const [loading, setLoading] = useState(enabled)
	const [error, setError] = useState<ApiError | null>(null)
	const [refreshIndex, setRefreshIndex] = useState(0)
	const params = useMemo(() => ({ week_start: weekStart, timezone }), [weekStart, timezone])

	const refetch = useCallback(() => {
		setRefreshIndex((previous) => previous + 1)
	}, [])

	useEffect(() => {
		if (!enabled) {
			setLoading(false)
			return undefined
		}

		const controller = new AbortController()

		setData(null)
		setLoading(true)
		setError(null)

		apiClient
			.getWeeklyAnalytics(params, controller.signal)
			.then((response) => {
				if (controller.signal.aborted) {
					return
				}

				if (!isWeeklyAnalyticsReport(response.data)) {
					throw invalidAnalyticsResponse()
				}

				setData(response.data)
				setLoading(false)
			})
			.catch((analyticsError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(analyticsError))
				setData(null)
				setLoading(false)
			})

		return () => {
			controller.abort()
		}
	}, [enabled, params, refreshIndex])

	return {
		data,
		loading,
		error,
		refetch,
	}
}
