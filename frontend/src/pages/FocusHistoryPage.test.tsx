import '@testing-library/jest-dom/vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useFocusHistory } from '../hooks/useFocusHistory'
import type { UseFocusHistoryReturn } from '../hooks/useFocusHistory'
import type { FocusSession } from '../types/api'
import { FocusHistoryScreen } from './FocusHistoryPage'

vi.mock('../hooks/useFocusHistory', () => ({
	useFocusHistory: vi.fn(),
}))

const useFocusHistoryMock = vi.mocked(useFocusHistory)

function renderScreen() {
	return render(
		<MemoryRouter>
			<FocusHistoryScreen />
		</MemoryRouter>,
	)
}

function makeSession(overrides: Partial<FocusSession> = {}): FocusSession {
	return {
		id: 'session-1',
		status: 'completed',
		topic: 'React hooks',
		started_at: '2026-05-01T10:00:00',
		ended_at: '2026-05-01T10:25:00',
		planned_duration_minutes: 25,
		actual_duration_seconds: 1500,
		difficulty: 4,
		notes: 'Review useEffect dependencies',
		...overrides,
	}
}

function mockHistory(overrides: Partial<UseFocusHistoryReturn> = {}) {
	const value: UseFocusHistoryReturn = {
		items: [],
		total: 0,
		limit: 20,
		offset: 0,
		loading: false,
		loadingMore: false,
		error: null,
		hasMore: false,
		refetch: vi.fn(),
		loadMore: vi.fn(),
		...overrides,
	}

	useFocusHistoryMock.mockReturnValue(value)
	return value
}

describe('FocusHistoryScreen', () => {
	afterEach(() => {
		vi.clearAllMocks()
	})

	it('shows loading state', () => {
		mockHistory({ loading: true })

		renderScreen()

		expect(screen.getByLabelText('Loading focus history')).toBeInTheDocument()
	})

	it('shows an empty state', () => {
		mockHistory()

		renderScreen()

		expect(screen.getByText('No sessions for this day')).toBeInTheDocument()
	})

	it('shows an error state with retry', async () => {
		const user = userEvent.setup()
		const refetch = vi.fn()
		mockHistory({
			error: { detail: 'Backend exploded', status: 500 },
			refetch,
		})

		renderScreen()

		expect(screen.getByText('Backend exploded')).toBeInTheDocument()
		await user.click(screen.getByText('Retry'))
		expect(refetch).toHaveBeenCalledTimes(1)
	})

	it('renders a completed session card', () => {
		mockHistory({
			items: [makeSession()],
			total: 1,
		})

		renderScreen()

		expect(screen.getByText('React hooks')).toBeInTheDocument()
		expect(screen.getByText('25 min of 25 min')).toBeInTheDocument()
		expect(screen.getByText('Completed')).toBeInTheDocument()
		expect(screen.getByText('Difficulty: 4/5')).toBeInTheDocument()
		expect(screen.getByText('Review useEffect dependencies')).toBeInTheDocument()
	})

	it('renders an active session without an end time', () => {
		const startedAt = new Date(Date.now() - 65_000).toISOString()
		mockHistory({
			items: [
				makeSession({
					id: 'active-session',
					status: 'active',
					topic: null,
					started_at: startedAt,
					ended_at: null,
					actual_duration_seconds: null,
					difficulty: null,
					notes: null,
				}),
			],
			total: 1,
		})

		renderScreen()

		expect(screen.getByText('No topic')).toBeInTheDocument()
		expect(screen.getByText('In progress')).toBeInTheDocument()
		expect(screen.getByText(/1 min of 25 min/)).toBeInTheDocument()
	})

	it('calls loadMore from the load more button', async () => {
		const user = userEvent.setup()
		const loadMore = vi.fn()
		mockHistory({
			items: [makeSession()],
			total: 2,
			hasMore: true,
			loadMore,
		})

		renderScreen()

		await user.click(screen.getByText('Load more'))
		expect(loadMore).toHaveBeenCalledTimes(1)
	})

	it('requests history for a changed date', () => {
		mockHistory()

		renderScreen()

		fireEvent.change(screen.getByLabelText('Choose date'), { target: { value: '2026-04-30' } })

		expect(useFocusHistoryMock).toHaveBeenLastCalledWith(
			expect.objectContaining({
				date: '2026-04-30',
				limit: 20,
				offset: 0,
			}),
		)
	})
})
