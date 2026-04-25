import { useCallback, useEffect, useRef, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { FocusSession } from '../types/api'

export const POMODORO_SECONDS = 25 * 60

type PomodoroStatus = 'idle' | 'running' | 'finished'

interface PomodoroState {
	status: PomodoroStatus
	session: FocusSession | null
	topic: string
	elapsed: number
	remaining: number
	progress: number
	loading: boolean
	error: string | null
}

interface UsePomodoroReturn extends PomodoroState {
	start: (topic: string, stageId?: string) => Promise<void>
	stop: (difficulty: number) => Promise<void>
	reset: () => void
}

function clampProgress(value: number): number {
	return Math.min(1, Math.max(0, value))
}

function getTimerValues(startedAt: string): Pick<PomodoroState, 'elapsed' | 'remaining' | 'progress'> {
	const startedAtMs = new Date(startedAt).getTime()
	const safeStartedAtMs = Number.isNaN(startedAtMs) ? Date.now() : startedAtMs
	const elapsed = Math.max(0, Math.floor((Date.now() - safeStartedAtMs) / 1000))
	const remaining = Math.max(0, POMODORO_SECONDS - elapsed)
	const progress = clampProgress(elapsed / POMODORO_SECONDS)

	return {
		elapsed,
		remaining,
		progress,
	}
}

export function usePomodoro(): UsePomodoroReturn {
	const [status, setStatus] = useState<PomodoroStatus>('idle')
	const [session, setSession] = useState<FocusSession | null>(null)
	const [topic, setTopic] = useState('')
	const [elapsed, setElapsed] = useState(0)
	const [remaining, setRemaining] = useState(POMODORO_SECONDS)
	const [progress, setProgress] = useState(0)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const actionInFlightRef = useRef(false)

	const applySession = useCallback((nextSession: FocusSession | null) => {
		if (!nextSession) {
			setStatus('idle')
			setSession(null)
			setTopic('')
			setElapsed(0)
			setRemaining(POMODORO_SECONDS)
			setProgress(0)
			return
		}

		const nextTimer = getTimerValues(nextSession.started_at)

		setSession(nextSession)
		setTopic(nextSession.topic)
		setElapsed(nextTimer.elapsed)
		setRemaining(nextTimer.remaining)
		setProgress(nextTimer.progress)
		setStatus(nextTimer.remaining === 0 ? 'finished' : 'running')
	}, [])

	useEffect(() => {
		let mounted = true
		let inFlight = false
		let initialPoll = true

		const pollActiveSession = async () => {
			if (inFlight || actionInFlightRef.current) {
				return
			}

			inFlight = true

			try {
				const response = await apiClient.getActiveSession()

				if (!mounted) {
					return
				}

				applySession(response.data)
				setError(null)
			} catch (pollError) {
				if (!mounted) {
					return
				}

				const normalizedError = normalizeApiError(pollError)

				if (normalizedError.status === 404) {
					applySession(null)
				} else {
					setError(normalizedError.detail)
				}
			} finally {
				if (mounted && initialPoll) {
					setLoading(false)
					initialPoll = false
				}

				inFlight = false
			}
		}

		void pollActiveSession()
		const intervalId = window.setInterval(pollActiveSession, 5000)

		return () => {
			mounted = false
			window.clearInterval(intervalId)
		}
	}, [applySession])

	useEffect(() => {
		if (status !== 'running' || !session) {
			return
		}

		const updateTimer = () => {
			const nextTimer = getTimerValues(session.started_at)

			setElapsed(nextTimer.elapsed)
			setRemaining(nextTimer.remaining)
			setProgress(nextTimer.progress)

			if (nextTimer.remaining === 0) {
				setStatus('finished')
			}
		}

		updateTimer()
		const intervalId = window.setInterval(updateTimer, 1000)

		return () => {
			window.clearInterval(intervalId)
		}
	}, [session, status])

	const start = useCallback(
		async (nextTopic: string, stageId?: string) => {
			actionInFlightRef.current = true
			setLoading(true)
			setError(null)

			try {
				const response = await apiClient.startFocus(nextTopic, stageId)
				applySession(response.data)
			} catch (startError) {
				const normalizedError = normalizeApiError(startError)
				setError(normalizedError.detail)
				throw normalizedError
			} finally {
				setLoading(false)
				actionInFlightRef.current = false
			}
		},
		[applySession],
	)

	const stop = useCallback(
		async (difficulty: number) => {
			if (!session) {
				applySession(null)
				return
			}

			actionInFlightRef.current = true
			setLoading(true)
			setError(null)

			try {
				await apiClient.endFocus(session.id, difficulty)
				applySession(null)
			} catch (stopError) {
				const normalizedError = normalizeApiError(stopError)
				setError(normalizedError.detail)
				throw normalizedError
			} finally {
				setLoading(false)
				actionInFlightRef.current = false
			}
		},
		[applySession, session],
	)

	const reset = useCallback(() => {
		applySession(null)
		setError(null)
	}, [applySession])

	return {
		status,
		session,
		topic,
		elapsed,
		remaining,
		progress,
		loading,
		error,
		start,
		stop,
		reset,
	}
}
