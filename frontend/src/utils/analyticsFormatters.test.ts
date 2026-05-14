import { describe, expect, it } from 'vitest'
import {
	formatMinutes,
	formatPercent,
	formatStreak,
	getTodayDateString,
	getWeekStart,
	getYesterdayDateString,
	isFutureDate,
	isFutureWeek,
	shiftDate,
	shiftWeek,
	toApiDate,
} from './analyticsFormatters'

describe('analytics formatters', () => {
	it('formats focus minutes', () => {
		expect(formatMinutes(95)).toBe('1ч 35м')
		expect(formatMinutes(25)).toBe('25м')
		expect(formatMinutes(0)).toBe('0м')
		expect(formatMinutes(null)).toBe('0м')
	})

	it('formats percent values', () => {
		expect(formatPercent(80)).toBe('80%')
		expect(formatPercent(null)).toBe('—')
		expect(formatPercent(undefined)).toBe('—')
	})

	it('formats streak with Russian plural forms', () => {
		expect(formatStreak(1)).toBe('1 день')
		expect(formatStreak(2)).toBe('2 дня')
		expect(formatStreak(5)).toBe('5 дней')
		expect(formatStreak(21)).toBe('21 день')
	})
})

describe('analytics date helpers', () => {
	it('uses local YYYY-MM-DD dates', () => {
		const now = new Date(2026, 4, 9, 12, 0, 0)

		expect(toApiDate(now)).toBe('2026-05-09')
		expect(getTodayDateString(now)).toBe('2026-05-09')
		expect(getYesterdayDateString(now)).toBe('2026-05-08')
	})

	it('shifts dates and weeks', () => {
		expect(shiftDate('2026-05-09', -1)).toBe('2026-05-08')
		expect(shiftWeek('2026-05-04', -1)).toBe('2026-04-27')
	})

	it('starts weeks on Monday', () => {
		expect(getWeekStart('2026-05-09')).toBe('2026-05-04')
		expect(getWeekStart('2026-05-10')).toBe('2026-05-04')
		expect(getWeekStart('2026-05-11')).toBe('2026-05-11')
	})

	it('detects future periods', () => {
		expect(isFutureDate('2026-05-10', '2026-05-09')).toBe(true)
		expect(isFutureDate('2026-05-09', '2026-05-09')).toBe(false)
		expect(isFutureWeek('2026-05-11', '2026-05-09')).toBe(true)
		expect(isFutureWeek('2026-05-04', '2026-05-09')).toBe(false)
	})
})
