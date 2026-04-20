import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { DailyPlan, PlanStage } from '../types/api'

export interface UseTodayPlanReturn {
	plan: DailyPlan | null
	stage: PlanStage | null
	loading: boolean
	error: string | null
	refetch: () => void
	markBlockDone: (blockIndex: number) => void
	completedBlocks: number[]
}

function getTodayStorageKey(date: Date): string {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')

	return `completed_blocks_${year}-${month}-${day}`
}

function sanitizeCompletedBlocks(value: unknown): number[] {
	if (!Array.isArray(value)) {
		return []
	}

	return Array.from(
		new Set(
			value.filter((item): item is number => Number.isInteger(item) && item >= 0),
		),
	).sort((left, right) => left - right)
}

function readCompletedBlocks(storageKey: string): number[] {
	if (typeof window === 'undefined') {
		return []
	}

	try {
		const raw = window.sessionStorage.getItem(storageKey)

		if (!raw) {
			return []
		}

		return sanitizeCompletedBlocks(JSON.parse(raw))
	} catch {
		return []
	}
}

function writeCompletedBlocks(storageKey: string, blockIndexes: number[]): void {
	if (typeof window === 'undefined') {
		return
	}

	try {
		window.sessionStorage.setItem(storageKey, JSON.stringify(blockIndexes))
	} catch {
		// Ignore storage write failures to avoid breaking the screen.
	}
}

function getCurrentStage(stages: PlanStage[] | undefined): PlanStage | null {
	return stages?.find((candidate) => candidate.status === 'in_progress') ?? null
}

export function useTodayPlan(): UseTodayPlanReturn {
	const storageKey = useMemo(() => getTodayStorageKey(new Date()), [])
	const [plan, setPlan] = useState<DailyPlan | null>(null)
	const [stage, setStage] = useState<PlanStage | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<string | null>(null)
	const [refreshIndex, setRefreshIndex] = useState(0)
	const [completedBlocks, setCompletedBlocks] = useState<number[]>([])

	const refetch = useCallback(() => {
		setRefreshIndex((previous) => previous + 1)
	}, [])

	useEffect(() => {
		const controller = new AbortController()

		setLoading(true)
		setError(null)

		Promise.allSettled([
			apiClient.getToday(controller.signal),
			apiClient.getCurrentPlan(controller.signal),
		]).then((results) => {
			if (controller.signal.aborted) {
				return
			}

			const [todayResult, currentPlanResult] = results

			if (todayResult.status === 'rejected') {
				const normalizedError = normalizeApiError(todayResult.reason)

				if (normalizedError.status === 404) {
					setPlan(null)
					setStage(null)
					setError(null)
					setLoading(false)
					return
				}

				setPlan(null)
				setStage(null)
				setError(normalizedError.detail)
				setLoading(false)
				return
			}

			setPlan(todayResult.value.data)

			if (currentPlanResult.status === 'fulfilled') {
				setStage(getCurrentStage(currentPlanResult.value.data?.stages))
			} else {
				const normalizedError = normalizeApiError(currentPlanResult.reason)
				setStage(normalizedError.status === 404 ? null : null)
			}

			setLoading(false)
		})

		return () => {
			controller.abort()
		}
	}, [refreshIndex])

	useEffect(() => {
		if (!plan) {
			setCompletedBlocks([])
			return
		}

		const sanitizedBlocks = readCompletedBlocks(storageKey).filter((blockIndex) => blockIndex < plan.blocks.length)
		setCompletedBlocks(sanitizedBlocks)
		writeCompletedBlocks(storageKey, sanitizedBlocks)
	}, [plan, storageKey])

	const markBlockDone = useCallback(
		(blockIndex: number) => {
			if (!plan || blockIndex < 0 || blockIndex >= plan.blocks.length) {
				return
			}

			setCompletedBlocks((previous) => {
				if (previous.includes(blockIndex)) {
					return previous
				}

				const nextCompletedBlocks = [...previous, blockIndex].sort((left, right) => left - right)
				writeCompletedBlocks(storageKey, nextCompletedBlocks)
				return nextCompletedBlocks
			})
		},
		[plan, storageKey],
	)

	return {
		plan,
		stage,
		loading,
		error,
		refetch,
		markBlockDone,
		completedBlocks,
	}
}
