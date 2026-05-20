import type { DailyBreakdownItem } from '../../types/api'
import { getWeekStart, shiftDate } from '../../utils/analyticsFormatters'

export interface WeeklyBreakdownSlot {
	date: string
	label: string
	focusMinutes: number
	sessionsCount: number
	completionRate: number | null
}

const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function normalizeItem(item: DailyBreakdownItem | undefined, date: string, index: number): WeeklyBreakdownSlot {
	return {
		date,
		label: WEEKDAY_LABELS[index],
		focusMinutes: Math.max(0, Math.round(item?.focus_minutes ?? 0)),
		sessionsCount: Math.max(0, Math.round(item?.sessions_count ?? 0)),
		completionRate: item?.completion_rate ?? null,
	}
}

export function buildWeeklyBreakdownSlots(
	dailyBreakdown: DailyBreakdownItem[] = [],
	weekStart?: string,
): WeeklyBreakdownSlot[] {
	const sortedBreakdown = [...dailyBreakdown].sort((left, right) => left.date.localeCompare(right.date))
	const start = weekStart ?? (sortedBreakdown[0] ? getWeekStart(sortedBreakdown[0].date) : undefined)
	const byDate = new Map(sortedBreakdown.map((item) => [item.date, item]))

	return WEEKDAY_LABELS.map((_, index) => {
		const date = start ? shiftDate(start, index) : ''
		return normalizeItem(date ? byDate.get(date) : undefined, date, index)
	})
}
