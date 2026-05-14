import { act, renderHook, waitFor } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '../lib/api'
import type { AnalyticsReportResponse, WeeklyAnalyticsReportResponse } from '../types/api'
import { useDailyAnalytics, useWeeklyAnalytics } from './useAnalytics'

function makeResponse<T>(data: T): AxiosResponse<T> {
	return { data } as AxiosResponse<T>
}

function makeDailyReport(overrides: Partial<AnalyticsReportResponse> = {}): AnalyticsReportResponse {
	return {
		period: {
			type: 'daily',
			start: '2026-05-01T00:00:00Z',
			end: '2026-05-02T00:00:00Z',
			timezone: 'UTC',
		},
		metrics: {
			total_focus_minutes: 95,
			sessions_count: 4,
			cancelled_sessions_count: 1,
			completion_rate: 80,
			average_session_minutes: 24,
			streak_days: 5,
			best_focus_hours: ['10:00'],
			most_focused_topics: [{ topic: 'FastAPI', minutes: 50 }],
		},
		summary: 'Daily summary',
		recommendations: ['Start with FastAPI'],
		data_quality: 'high',
		...overrides,
	}
}

function makeWeeklyReport(overrides: Partial<WeeklyAnalyticsReportResponse> = {}): WeeklyAnalyticsReportResponse {
	return {
		...makeDailyReport(),
		period: {
			type: 'weekly',
			start: '2026-04-27T00:00:00Z',
			end: '2026-05-04T00:00:00Z',
			timezone: 'UTC',
		},
		daily_breakdown: [
			{
				date: '2026-04-27',
				focus_minutes: 60,
				sessions_count: 3,
				completion_rate: 100,
			},
		],
		summary: 'Weekly summary',
		...overrides,
	}
}

describe('analytics hooks', () => {
	afterEach(() => {
		vi.restoreAllMocks()
	})

	it('loads daily analytics with date and timezone params', async () => {
		const getDailyAnalytics = vi
			.spyOn(apiClient, 'getDailyAnalytics')
			.mockResolvedValue(makeResponse(makeDailyReport()))

		const { result } = renderHook(() => useDailyAnalytics({ date: '2026-05-01', timezone: 'Europe/Dublin' }))

		await waitFor(() => expect(result.current.loading).toBe(false))

		expect(result.current.isLoading).toBe(false)
		expect(result.current.data?.metrics.total_focus_minutes).toBe(95)
		expect(getDailyAnalytics).toHaveBeenCalledWith(
			{ date: '2026-05-01', timezone: 'Europe/Dublin' },
			expect.any(AbortSignal),
		)
	})

	it('refetches daily analytics on demand', async () => {
		const getDailyAnalytics = vi
			.spyOn(apiClient, 'getDailyAnalytics')
			.mockResolvedValue(makeResponse(makeDailyReport()))

		const { result } = renderHook(() => useDailyAnalytics({ date: '2026-05-01' }))

		await waitFor(() => expect(result.current.loading).toBe(false))

		act(() => {
			result.current.refetch()
		})

		await waitFor(() => expect(getDailyAnalytics).toHaveBeenCalledTimes(2))
	})

	it('reloads weekly analytics when the week changes', async () => {
		const getWeeklyAnalytics = vi.spyOn(apiClient, 'getWeeklyAnalytics')
		getWeeklyAnalytics
			.mockResolvedValueOnce(makeResponse(makeWeeklyReport()))
			.mockResolvedValueOnce(
				makeResponse(
					makeWeeklyReport({
						period: {
							type: 'weekly',
							start: '2026-05-04T00:00:00Z',
							end: '2026-05-11T00:00:00Z',
							timezone: 'UTC',
						},
						daily_breakdown: [],
					}),
				),
			)

		const { result, rerender } = renderHook(({ weekStart }) => useWeeklyAnalytics({ weekStart }), {
			initialProps: { weekStart: '2026-04-27' },
		})

		await waitFor(() => expect(result.current.data?.period.start).toBe('2026-04-27T00:00:00Z'))

		rerender({ weekStart: '2026-05-04' })

		await waitFor(() => expect(result.current.data?.period.start).toBe('2026-05-04T00:00:00Z'))
		expect(getWeeklyAnalytics).toHaveBeenLastCalledWith(
			{ week_start: '2026-05-04', timezone: undefined },
			expect.any(AbortSignal),
		)
	})

	it('returns a normalized error for invalid response shape', async () => {
		vi.spyOn(apiClient, 'getDailyAnalytics').mockResolvedValue(makeResponse({ broken: true } as unknown as AnalyticsReportResponse))

		const { result } = renderHook(() => useDailyAnalytics({ date: '2026-05-01' }))

		await waitFor(() => expect(result.current.loading).toBe(false))

		expect(result.current.error?.detail).toBe('Invalid analytics response')
		expect(result.current.data).toBeNull()
	})
})
