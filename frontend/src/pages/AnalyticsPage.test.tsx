import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useDailyAnalytics, useWeeklyAnalytics } from '../hooks/useAnalytics'
import type { UseAnalyticsReportReturn } from '../hooks/useAnalytics'
import type { AnalyticsReportResponse, WeeklyAnalyticsReportResponse } from '../types/api'
import { AnalyticsPage } from './AnalyticsPage'

vi.mock('../hooks/useAnalytics', () => ({
	useDailyAnalytics: vi.fn(),
	useWeeklyAnalytics: vi.fn(),
}))

const useDailyAnalyticsMock = vi.mocked(useDailyAnalytics)
const useWeeklyAnalyticsMock = vi.mocked(useWeeklyAnalytics)

function makeDailyReport(overrides: Partial<AnalyticsReportResponse> = {}): AnalyticsReportResponse {
	return {
		period: {
			type: 'daily',
			start: '2026-05-09T00:00:00Z',
			end: '2026-05-10T00:00:00Z',
			timezone: 'UTC',
		},
		metrics: {
			total_focus_minutes: 95,
			sessions_count: 4,
			cancelled_sessions_count: 1,
			completion_rate: 80,
			average_session_minutes: 24,
			streak_days: 5,
			best_focus_hours: ['10:00', '14:00'],
			most_focused_topics: [{ topic: 'FastAPI', minutes: 50 }],
		},
		summary: 'Сегодня ты сфокусировался на 95 минут.',
		recommendations: ['Завтра начни с FastAPI.'],
		data_quality: 'high',
		...overrides,
	}
}

function makeWeeklyReport(overrides: Partial<WeeklyAnalyticsReportResponse> = {}): WeeklyAnalyticsReportResponse {
	return {
		...makeDailyReport(),
		period: {
			type: 'weekly',
			start: '2026-05-04T00:00:00Z',
			end: '2026-05-11T00:00:00Z',
			timezone: 'UTC',
		},
		metrics: {
			total_focus_minutes: 420,
			sessions_count: 18,
			cancelled_sessions_count: 3,
			completion_rate: 85,
			average_session_minutes: 23,
			streak_days: 5,
			best_focus_hours: ['09:00', '11:00', '19:00'],
			most_focused_topics: [
				{ topic: 'RAG', minutes: 160 },
				{ topic: 'PostgreSQL', minutes: 90 },
			],
		},
		daily_breakdown: [
			{ date: '2026-05-04', focus_minutes: 60, sessions_count: 3, completion_rate: 100 },
			{ date: '2026-05-05', focus_minutes: 0, sessions_count: 0, completion_rate: null },
			{ date: '2026-05-06', focus_minutes: 120, sessions_count: 4, completion_rate: 75 },
		],
		summary: 'На этой неделе ты набрал 420 минут фокуса.',
		recommendations: ['Твои лучшие часы — утро.'],
		data_quality: 'medium',
		...overrides,
	}
}

function mockDaily(overrides: Partial<UseAnalyticsReportReturn<AnalyticsReportResponse>> = {}) {
	const value: UseAnalyticsReportReturn<AnalyticsReportResponse> = {
		data: makeDailyReport(),
		loading: false,
		error: null,
		refetch: vi.fn(),
		...overrides,
	}

	useDailyAnalyticsMock.mockReturnValue(value)
	return value
}

function mockWeekly(overrides: Partial<UseAnalyticsReportReturn<WeeklyAnalyticsReportResponse>> = {}) {
	const value: UseAnalyticsReportReturn<WeeklyAnalyticsReportResponse> = {
		data: makeWeeklyReport(),
		loading: false,
		error: null,
		refetch: vi.fn(),
		...overrides,
	}

	useWeeklyAnalyticsMock.mockReturnValue(value)
	return value
}

describe('AnalyticsPage', () => {
	beforeEach(() => {
		vi.useFakeTimers()
		vi.setSystemTime(new Date('2026-05-09T12:00:00'))
		useDailyAnalyticsMock.mockReset()
		useWeeklyAnalyticsMock.mockReset()
		mockDaily()
		mockWeekly()
	})

	afterEach(() => {
		vi.useRealTimers()
		vi.clearAllMocks()
	})

	it('renders daily summary cards and analytics sections', () => {
		render(<AnalyticsPage />)

		expect(screen.getByText('Аналитика')).toBeInTheDocument()
		expect(screen.getByText('1ч 35м')).toBeInTheDocument()
		expect(screen.getByText('4')).toBeInTheDocument()
		expect(screen.getByText('5 дней')).toBeInTheDocument()
		expect(screen.getByText('80%')).toBeInTheDocument()
		expect(screen.getByText('FastAPI')).toBeInTheDocument()
		expect(screen.getByText('10:00')).toBeInTheDocument()
		expect(screen.getByText('Сегодня ты сфокусировался на 95 минут.')).toBeInTheDocument()
		expect(screen.getByText('Завтра начни с FastAPI.')).toBeInTheDocument()
		expect(screen.getByLabelText('Тепловая карта активности')).toBeInTheDocument()
	})

	it('switches to weekly charts, heatmap, topics, hours and summary', () => {
		render(<AnalyticsPage />)

		fireEvent.click(screen.getByRole('tab', { name: 'Неделя' }))

		expect(screen.getByText('Фокус по дням')).toBeInTheDocument()
		expect(screen.getByText('Сессии по дням')).toBeInTheDocument()
		expect(screen.getByText('RAG')).toBeInTheDocument()
		expect(screen.getByText('09:00')).toBeInTheDocument()
		expect(screen.getByText('На этой неделе ты набрал 420 минут фокуса.')).toBeInTheDocument()
		expect(screen.getByText('Данных достаточно')).toBeInTheDocument()
	})

	it('renders loading state', () => {
		mockDaily({ data: null, loading: true })

		render(<AnalyticsPage />)

		expect(screen.getByLabelText('Загрузка аналитики')).toBeInTheDocument()
	})

	it('renders an error state and retries', () => {
		const refetch = vi.fn()
		mockDaily({
			data: null,
			loading: false,
			error: { detail: 'Internal server error', status: 500 },
			refetch,
		})

		render(<AnalyticsPage />)

		expect(screen.getByText('Не удалось загрузить аналитику')).toBeInTheDocument()
		fireEvent.click(screen.getByText('Повторить'))
		expect(refetch).toHaveBeenCalledTimes(1)
	})

	it('renders empty daily and fallback AI summary states', () => {
		mockDaily({
			data: makeDailyReport({
				metrics: {
					total_focus_minutes: 0,
					sessions_count: 0,
					cancelled_sessions_count: 0,
					completion_rate: null,
					average_session_minutes: null,
					streak_days: 0,
					best_focus_hours: [],
					most_focused_topics: [],
				},
				summary: '',
				recommendations: [],
				data_quality: 'low',
			}),
		})

		render(<AnalyticsPage />)

		expect(screen.getByText('Сегодня пока нет фокус-сессий. Запусти один короткий блок — и графики оживут.')).toBeInTheDocument()
		expect(screen.getByText('Пока недостаточно данных для отчёта.')).toBeInTheDocument()
		expect(screen.getByText('Пока нет данных по темам')).toBeInTheDocument()
		expect(screen.getByText('Пока недостаточно данных')).toBeInTheDocument()
	})

	it('moves between daily periods and disables future day navigation', () => {
		render(<AnalyticsPage />)

		expect(screen.getByLabelText('Следующий день')).toBeDisabled()
		fireEvent.click(screen.getByLabelText('Предыдущий день'))

		expect(useDailyAnalyticsMock).toHaveBeenLastCalledWith(
			expect.objectContaining({
				date: '2026-05-08',
			}),
		)
	})

	it('moves between weekly periods and disables future week navigation', () => {
		render(<AnalyticsPage />)

		fireEvent.click(screen.getByRole('tab', { name: 'Неделя' }))
		expect(screen.getByLabelText('Следующая неделя')).toBeDisabled()
		fireEvent.click(screen.getByLabelText('Предыдущая неделя'))

		expect(useWeeklyAnalyticsMock).toHaveBeenLastCalledWith(
			expect.objectContaining({
				weekStart: '2026-04-27',
			}),
		)
	})
})
