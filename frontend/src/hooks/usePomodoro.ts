import { useCallback, useEffect, useRef, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { FocusSession } from '../types/api'

export const POMODORO_SECONDS = 25 * 60
export const MIN_POMODOROS = 1
export const MAX_POMODOROS = 5

type PomodoroStatus = 'idle' | 'running' | 'paused' | 'finished'

interface PomodoroState {
	status: PomodoroStatus
	session: FocusSession | null
	topic: string
	pomodoroCount: number
	totalSeconds: number
	elapsed: number
	remaining: number
	progress: number
	loading: boolean
	error: string | null
}

interface UsePomodoroReturn extends PomodoroState {
	start: (topic: string, stageId?: string, pomodoroCount?: number) => Promise<void>
	pause: () => void
	resume: () => void
	stop: (difficulty: number) => Promise<void>
	reset: () => void
}

function clampProgress(value: number): number {
	return Math.min(1, Math.max(0, value))
}

function normalizePomodoroCount(value: number | undefined): number {
	if (!Number.isFinite(value)) {
		return MIN_POMODOROS
	}

	return Math.min(MAX_POMODOROS, Math.max(MIN_POMODOROS, Math.round(value ?? MIN_POMODOROS)))
}

function getTimerValues(
	startedAt: string,
	totalSeconds: number,
	pausedSeconds = 0,
): Pick<PomodoroState, 'elapsed' | 'remaining' | 'progress'> {
	const startedAtMs = new Date(startedAt).getTime()
	const safeStartedAtMs = Number.isNaN(startedAtMs) ? Date.now() : startedAtMs
	const elapsed = Math.max(0, Math.floor((Date.now() - safeStartedAtMs) / 1000) - pausedSeconds)
	const remaining = Math.max(0, totalSeconds - elapsed)
	const progress = clampProgress(elapsed / totalSeconds)

	return {
		elapsed,
		remaining,
		progress,
	}
}

export function usePomodoro(initialPomodoroCount = MIN_POMODOROS): UsePomodoroReturn {
	const normalizedInitialCount = normalizePomodoroCount(initialPomodoroCount)
	const initialTotalSeconds = normalizedInitialCount * POMODORO_SECONDS
	const [status, setStatus] = useState<PomodoroStatus>('idle')
	const [session, setSession] = useState<FocusSession | null>(null)
	const [topic, setTopic] = useState('')
	const [pomodoroCount, setPomodoroCount] = useState(normalizedInitialCount)
	const [totalSeconds, setTotalSeconds] = useState(initialTotalSeconds)
	const [elapsed, setElapsed] = useState(0)
	const [remaining, setRemaining] = useState(initialTotalSeconds)
	const [progress, setProgress] = useState(0)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const actionInFlightRef = useRef(false)
	const pausedSecondsRef = useRef(0)
	const pauseStartedAtRef = useRef<number | null>(null)
	const statusRef = useRef(status)
	const sessionRef = useRef(session)
	const pomodoroCountRef = useRef(pomodoroCount)
	const totalSecondsRef = useRef(totalSeconds)

	useEffect(() => {
		statusRef.current = status
	}, [status])

	useEffect(() => {
		sessionRef.current = session
	}, [session])

	useEffect(() => {
		pomodoroCountRef.current = pomodoroCount
		totalSecondsRef.current = totalSeconds
	}, [pomodoroCount, totalSeconds])

	const applyPomodoroCount = useCallback((nextPomodoroCount: number) => {
		const nextCount = normalizePomodoroCount(nextPomodoroCount)
		const nextTotalSeconds = nextCount * POMODORO_SECONDS

		setPomodoroCount(nextCount)
		setTotalSeconds(nextTotalSeconds)
		pomodoroCountRef.current = nextCount
		totalSecondsRef.current = nextTotalSeconds

		if (statusRef.current === 'idle') {
			setElapsed(0)
			setRemaining(nextTotalSeconds)
			setProgress(0)
		}
	}, [])

	const applySession = useCallback((nextSession: FocusSession | null) => {
		if (!nextSession) {
			setStatus('idle')
			setSession(null)
			setTopic('')
			setElapsed(0)
			setRemaining(totalSecondsRef.current)
			setProgress(0)
			pausedSecondsRef.current = 0
			pauseStartedAtRef.current = null
			return
		}

		const isSameSession = sessionRef.current?.id === nextSession.id

		if (!isSameSession) {
			pausedSecondsRef.current = 0
			pauseStartedAtRef.current = null
		}

		if (statusRef.current === 'paused' && isSameSession) {
			setSession(nextSession)
			setTopic(nextSession.topic)
			return
		}

		const nextTimer = getTimerValues(nextSession.started_at, totalSecondsRef.current, pausedSecondsRef.current)

		setSession(nextSession)
		setTopic(nextSession.topic)
		setElapsed(nextTimer.elapsed)
		setRemaining(nextTimer.remaining)
		setProgress(nextTimer.progress)
		setStatus(nextTimer.remaining === 0 ? 'finished' : 'running')
	}, [])

	useEffect(() => {
		if (status === 'idle') {
			applyPomodoroCount(initialPomodoroCount)
		}
	}, [applyPomodoroCount, initialPomodoroCount, status])

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
			const nextTimer = getTimerValues(session.started_at, totalSecondsRef.current, pausedSecondsRef.current)

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
		async (nextTopic: string, stageId?: string, nextPomodoroCount?: number) => {
			applyPomodoroCount(nextPomodoroCount ?? pomodoroCountRef.current)
			pausedSecondsRef.current = 0
			pauseStartedAtRef.current = null
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
		[applyPomodoroCount, applySession],
	)

	const pause = useCallback(() => {
		const currentSession = sessionRef.current

		if (statusRef.current !== 'running' || !currentSession) {
			return
		}

		const nextTimer = getTimerValues(currentSession.started_at, totalSecondsRef.current, pausedSecondsRef.current)

		setElapsed(nextTimer.elapsed)
		setRemaining(nextTimer.remaining)
		setProgress(nextTimer.progress)

		if (nextTimer.remaining === 0) {
			setStatus('finished')
			return
		}

		pauseStartedAtRef.current = Date.now()
		setStatus('paused')
	}, [])

	const resume = useCallback(() => {
		const currentSession = sessionRef.current

		if (statusRef.current !== 'paused' || !currentSession) {
			return
		}

		const pauseStartedAt = pauseStartedAtRef.current

		if (pauseStartedAt) {
			pausedSecondsRef.current += Math.max(0, Math.floor((Date.now() - pauseStartedAt) / 1000))
		}

		pauseStartedAtRef.current = null

		const nextTimer = getTimerValues(currentSession.started_at, totalSecondsRef.current, pausedSecondsRef.current)

		setElapsed(nextTimer.elapsed)
		setRemaining(nextTimer.remaining)
		setProgress(nextTimer.progress)
		setStatus(nextTimer.remaining === 0 ? 'finished' : 'running')
	}, [])

	const stop = useCallback(
		async (difficulty: number) => {
			if (!session) {
				applySession(null)
				return
			}

			if (pauseStartedAtRef.current) {
				pausedSecondsRef.current += Math.max(0, Math.floor((Date.now() - pauseStartedAtRef.current) / 1000))
				pauseStartedAtRef.current = null
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
		pomodoroCount,
		totalSeconds,
		elapsed,
		remaining,
		progress,
		loading,
		error,
		start,
		pause,
		resume,
		stop,
		reset,
	}
}
