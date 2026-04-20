import { useCallback, useEffect, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { ApiError, FocusSession } from '../types/api'

export interface FocusState {
	session: FocusSession | null
	isActive: boolean
	startedAt: Date | null
	elapsed: number
}

export function useFocus(): FocusState & {
	start: (topic: string, stageId?: string) => Promise<void>
	end: (difficulty: number) => Promise<void>
	loading: boolean
	error: ApiError | null
} {
	const [session, setSession] = useState<FocusSession | null>(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<ApiError | null>(null)
	const [startedAt, setStartedAt] = useState<Date | null>(null)
	const [elapsed, setElapsed] = useState(0)

	const isActive = Boolean(session && startedAt)

	useEffect(() => {
		if (!startedAt) {
			setElapsed(0)
			return
		}

		const updateElapsed = () => {
			setElapsed(Math.max(0, Math.floor((Date.now() - startedAt.getTime()) / 1000)))
		}

		updateElapsed()
		const intervalId = window.setInterval(updateElapsed, 1000)

		return () => {
			window.clearInterval(intervalId)
		}
	}, [startedAt])

	const start = useCallback(async (topic: string, stageId?: string) => {
		setLoading(true)
		setError(null)

		try {
			const response = await apiClient.startFocus(topic, stageId)
			const nextSession = response.data
			const sessionStart = nextSession.started_at ? new Date(nextSession.started_at) : new Date()

			setSession(nextSession)
			setStartedAt(sessionStart)
			setElapsed(0)
		} catch (focusError) {
			const normalizedError = normalizeApiError(focusError)
			setError(normalizedError)
			throw normalizedError
		} finally {
			setLoading(false)
		}
	}, [])

	const end = useCallback(
		async (difficulty: number) => {
			if (!session) {
				return
			}

			setLoading(true)
			setError(null)

			try {
				await apiClient.endFocus(session.id, difficulty)
				setSession(null)
				setStartedAt(null)
				setElapsed(0)
			} catch (focusError) {
				const normalizedError = normalizeApiError(focusError)
				setError(normalizedError)
				throw normalizedError
			} finally {
				setLoading(false)
			}
		},
		[session],
	)

	return {
		session,
		isActive,
		startedAt,
		elapsed,
		start,
		end,
		loading,
		error,
	}
}
