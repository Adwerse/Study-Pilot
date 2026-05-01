import { act, renderHook, waitFor } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '../lib/api'
import type { FocusHistoryResponse, FocusSession } from '../types/api'
import { useFocusHistory } from './useFocusHistory'

function makeSession(id: string, startedAt: string): FocusSession {
	return {
		id,
		status: 'completed',
		topic: `Topic ${id}`,
		started_at: startedAt,
		ended_at: startedAt,
		planned_duration_minutes: 25,
		actual_duration_seconds: 1500,
		difficulty: 3,
	}
}

function makeResponse(payload: FocusHistoryResponse): AxiosResponse<FocusHistoryResponse> {
	return { data: payload } as AxiosResponse<FocusHistoryResponse>
}

describe('useFocusHistory', () => {
	afterEach(() => {
		vi.restoreAllMocks()
	})

	it('loads more sessions with the next offset', async () => {
		const getFocusHistory = vi.spyOn(apiClient, 'getFocusHistory')
		getFocusHistory
			.mockResolvedValueOnce(
				makeResponse({
					items: [makeSession('1', '2026-05-01T10:00:00Z')],
					total: 2,
					limit: 1,
					offset: 0,
				}),
			)
			.mockResolvedValueOnce(
				makeResponse({
					items: [makeSession('2', '2026-05-01T11:00:00Z')],
					total: 2,
					limit: 1,
					offset: 1,
				}),
			)

		const { result } = renderHook(() => useFocusHistory({ date: '2026-05-01', limit: 1 }))

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.items).toHaveLength(1)

		act(() => {
			result.current.loadMore()
		})

		await waitFor(() => expect(result.current.items).toHaveLength(2))
		expect(getFocusHistory).toHaveBeenNthCalledWith(
			1,
			expect.objectContaining({ date: '2026-05-01', limit: 1, offset: 0 }),
			expect.any(AbortSignal),
		)
		expect(getFocusHistory).toHaveBeenNthCalledWith(
			2,
			expect.objectContaining({ date: '2026-05-01', limit: 1, offset: 1 }),
			expect.any(AbortSignal),
		)
	})

	it('reloads history when the date changes', async () => {
		const getFocusHistory = vi.spyOn(apiClient, 'getFocusHistory')
		getFocusHistory
			.mockResolvedValueOnce(
				makeResponse({
					items: [makeSession('1', '2026-05-01T10:00:00Z')],
					total: 1,
					limit: 20,
					offset: 0,
				}),
			)
			.mockResolvedValueOnce(
				makeResponse({
					items: [makeSession('2', '2026-05-02T10:00:00Z')],
					total: 1,
					limit: 20,
					offset: 0,
				}),
			)

		const { result, rerender } = renderHook(({ date }) => useFocusHistory({ date }), {
			initialProps: { date: '2026-05-01' },
		})

		await waitFor(() => expect(result.current.items[0]?.id).toBe('1'))

		rerender({ date: '2026-05-02' })

		await waitFor(() => expect(result.current.items[0]?.id).toBe('2'))
		expect(getFocusHistory).toHaveBeenLastCalledWith(
			expect.objectContaining({ date: '2026-05-02', offset: 0 }),
			expect.any(AbortSignal),
		)
	})
})
