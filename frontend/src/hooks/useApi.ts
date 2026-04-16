import { useCallback, useEffect, useState } from 'react'
import { normalizeApiError } from '../lib/api'
import type { ApiError } from '../types/api'

export interface UseApiState<T> {
	data: T | null
	loading: boolean
	error: ApiError | null
}

type ApiFetcher<T> = (signal?: AbortSignal) => Promise<{ data: T }>

export function useApi<T>(
	fetcher: ApiFetcher<T>,
	deps: unknown[] = [],
): UseApiState<T> & { refetch: () => void } {
	const [data, setData] = useState<T | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState<ApiError | null>(null)
	const [refreshIndex, setRefreshIndex] = useState(0)

	const refetch = useCallback(() => {
		setRefreshIndex((prev) => prev + 1)
	}, [])

	useEffect(() => {
		const controller = new AbortController()

		setLoading(true)
		setError(null)

		fetcher(controller.signal)
			.then((response) => {
				if (controller.signal.aborted) {
					return
				}

				setData(response.data)
				setLoading(false)
			})
			.catch((fetchError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(fetchError))
				setLoading(false)
			})

		return () => {
			controller.abort()
		}
	}, [fetcher, refreshIndex, ...deps])

	return {
		data,
		loading,
		error,
		refetch,
	}
}
