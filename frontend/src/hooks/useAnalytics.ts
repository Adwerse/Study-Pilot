import { useCallback, useEffect, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { ApiError, DailyMetrics } from '../types/api'

export function useAnalytics(): {
	daily: DailyMetrics | null
	weekly: DailyMetrics[]
	streak: number
	loading: boolean
	error: ApiError | null
} {
	const [daily, setDaily] = useState<DailyMetrics | null>(null)
	const [weekly, setWeekly] = useState<DailyMetrics[]>([])
	const [streak, setStreak] = useState(0)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<ApiError | null>(null)

	const fetchAnalytics = useCallback(async (signal?: AbortSignal) => {
		const [dailyResponse, weeklyResponse, streakResponse] = await Promise.all([
			apiClient.getDailyMetrics(signal),
			apiClient.getWeeklyMetrics(signal),
			apiClient.getStreak(signal),
		])

		return {
			daily: dailyResponse.data,
			weekly: weeklyResponse.data,
			streak: streakResponse.data.streak_days,
		}
	}, [])

	useEffect(() => {
		const controller = new AbortController()

		setLoading(true)
		setError(null)

		fetchAnalytics(controller.signal)
			.then((payload) => {
				if (controller.signal.aborted) {
					return
				}

				setDaily(payload.daily)
				setWeekly(payload.weekly)
				setStreak(payload.streak)
				setLoading(false)
			})
			.catch((analyticsError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(analyticsError))
				setLoading(false)
			})

		return () => {
			controller.abort()
		}
	}, [fetchAnalytics])

	return {
		daily,
		weekly,
		streak,
		loading,
		error,
	}
}
