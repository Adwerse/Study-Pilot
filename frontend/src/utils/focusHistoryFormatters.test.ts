import { describe, expect, it } from 'vitest'
import { formatDifficulty, formatDuration, formatSessionTimeRange, formatStatus } from './focusHistoryFormatters'

describe('focus history formatters', () => {
	it('formats duration in minutes and hours', () => {
		expect(formatDuration(1500)).toBe('25 min')
		expect(formatDuration(3660)).toBe('1 h 1 min')
		expect(formatDuration(30)).toBe('<1 min')
	})

	it('formats focus statuses', () => {
		expect(formatStatus('active')).toBe('In progress')
		expect(formatStatus('completed')).toBe('Completed')
		expect(formatStatus('cancelled')).toBe('Cancelled')
	})

	it('formats difficulty when present', () => {
		expect(formatDifficulty(4)).toBe('4/5')
		expect(formatDifficulty(null)).toBeNull()
	})

	it('formats a local time range', () => {
		expect(formatSessionTimeRange('2026-05-01T10:00:00', '2026-05-01T10:25:00')).toBe('10:00–10:25')
		expect(formatSessionTimeRange('2026-05-01T10:00:00', null)).toBe('10:00–now')
	})
})
