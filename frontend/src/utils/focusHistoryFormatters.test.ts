import { describe, expect, it } from 'vitest'
import { formatDifficulty, formatDuration, formatSessionTimeRange, formatStatus } from './focusHistoryFormatters'

describe('focus history formatters', () => {
	it('formats duration in minutes and hours', () => {
		expect(formatDuration(1500)).toBe('25 мин')
		expect(formatDuration(3660)).toBe('1 ч 1 мин')
		expect(formatDuration(30)).toBe('<1 мин')
	})

	it('formats focus statuses', () => {
		expect(formatStatus('active')).toBe('В процессе')
		expect(formatStatus('completed')).toBe('Завершена')
		expect(formatStatus('cancelled')).toBe('Отменена')
	})

	it('formats difficulty when present', () => {
		expect(formatDifficulty(4)).toBe('4/5')
		expect(formatDifficulty(null)).toBeNull()
	})

	it('formats a local time range', () => {
		expect(formatSessionTimeRange('2026-05-01T10:00:00', '2026-05-01T10:25:00')).toBe('10:00–10:25')
		expect(formatSessionTimeRange('2026-05-01T10:00:00', null)).toBe('10:00–сейчас')
	})
})
