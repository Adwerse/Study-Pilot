import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { ApiError, FocusSession, FocusSessionStatus } from '../types/api'

export interface UseFocusHistoryParams {
	date?: string
	status?: FocusSessionStatus
	limit?: number
	offset?: number
}

export interface UseFocusHistoryReturn {
	items: FocusSession[]
	total: number
	limit: number
	offset: number
	loading: boolean
	loadingMore: boolean
	error: ApiError | null
	hasMore: boolean
	refetch: () => void
	loadMore: () => void
}

interface FocusHistoryQuery {
	date?: string
	status?: FocusSessionStatus
	limit: number
	initialOffset: number
	pageOffset: number
	refreshIndex: number
}

function normalizePositiveInteger(value: number | undefined, fallback: number, max?: number): number {
	if (!Number.isFinite(value)) {
		return fallback
	}

	const normalized = Math.max(1, Math.round(value ?? fallback))
	return max ? Math.min(max, normalized) : normalized
}

function createQuery(params: UseFocusHistoryParams): FocusHistoryQuery {
	const limit = normalizePositiveInteger(params.limit, 20, 100)
	const initialOffset = Math.max(0, Math.round(params.offset ?? 0))

	return {
		date: params.date,
		status: params.status,
		limit,
		initialOffset,
		pageOffset: initialOffset,
		refreshIndex: 0,
	}
}

function queryMatchesParams(query: FocusHistoryQuery, params: UseFocusHistoryParams): boolean {
	const limit = normalizePositiveInteger(params.limit, 20, 100)
	const initialOffset = Math.max(0, Math.round(params.offset ?? 0))

	return (
		query.date === params.date &&
		query.status === params.status &&
		query.limit === limit &&
		query.initialOffset === initialOffset
	)
}

function appendUniqueSessions(previous: FocusSession[], next: FocusSession[]): FocusSession[] {
	const seenIds = new Set(previous.map((item) => item.id))
	const uniqueNext = next.filter((item) => {
		if (seenIds.has(item.id)) {
			return false
		}

		seenIds.add(item.id)
		return true
	})

	return [...previous, ...uniqueNext]
}

export function useFocusHistory(params: UseFocusHistoryParams): UseFocusHistoryReturn {
	const stableParams = useMemo(
		() => ({
			date: params.date,
			status: params.status,
			limit: params.limit,
			offset: params.offset,
		}),
		[params.date, params.limit, params.offset, params.status],
	)
	const [query, setQuery] = useState<FocusHistoryQuery>(() => createQuery(stableParams))
	const [items, setItems] = useState<FocusSession[]>([])
	const [total, setTotal] = useState(0)
	const [responseLimit, setResponseLimit] = useState(query.limit)
	const [responseOffset, setResponseOffset] = useState(query.initialOffset)
	const [loading, setLoading] = useState(true)
	const [loadingMore, setLoadingMore] = useState(false)
	const [error, setError] = useState<ApiError | null>(null)

	useEffect(() => {
		setQuery((previous) => {
			if (queryMatchesParams(previous, stableParams)) {
				return previous
			}

			return createQuery(stableParams)
		})
		setItems([])
		setTotal(0)
		setError(null)
	}, [stableParams])

	useEffect(() => {
		const controller = new AbortController()
		const isFirstPage = query.pageOffset === query.initialOffset

		if (isFirstPage) {
			setLoading(true)
		} else {
			setLoadingMore(true)
		}
		setError(null)

		apiClient
			.getFocusHistory(
				{
					date: query.date,
					status: query.status,
					limit: query.limit,
					offset: query.pageOffset,
				},
				controller.signal,
			)
			.then((response) => {
				if (controller.signal.aborted) {
					return
				}

				const payload = response.data

				setItems((previous) => (isFirstPage ? payload.items : appendUniqueSessions(previous, payload.items)))
				setTotal(payload.total)
				setResponseLimit(payload.limit)
				setResponseOffset(payload.offset)
				setLoading(false)
				setLoadingMore(false)
			})
			.catch((historyError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(historyError))
				setLoading(false)
				setLoadingMore(false)
			})

		return () => {
			controller.abort()
		}
	}, [query])

	const loadedThrough = query.initialOffset + items.length
	const hasMore = loadedThrough < total

	const refetch = useCallback(() => {
		setItems([])
		setQuery((previous) => ({
			...previous,
			pageOffset: previous.initialOffset,
			refreshIndex: previous.refreshIndex + 1,
		}))
	}, [])

	const loadMore = useCallback(() => {
		if (loading || loadingMore || !hasMore) {
			return
		}

		setQuery((previous) => ({
			...previous,
			pageOffset: responseOffset + responseLimit,
		}))
	}, [hasMore, loading, loadingMore, responseLimit, responseOffset])

	return {
		items,
		total,
		limit: responseLimit,
		offset: responseOffset,
		loading,
		loadingMore,
		error,
		hasMore,
		refetch,
		loadMore,
	}
}
