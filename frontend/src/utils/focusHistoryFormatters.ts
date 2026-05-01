import type { FocusSessionStatus } from '../types/api'

const timeFormatter = new Intl.DateTimeFormat(undefined, {
	hour: '2-digit',
	minute: '2-digit',
	hourCycle: 'h23',
})

function formatTime(value: string): string {
	const date = new Date(value)

	if (Number.isNaN(date.getTime())) {
		return '--:--'
	}

	return timeFormatter.format(date)
}

export function formatSessionTimeRange(startedAt: string, endedAt?: string | null): string {
	const startTime = formatTime(startedAt)
	const endTime = endedAt ? formatTime(endedAt) : 'now'

	return `${startTime}–${endTime}`
}

export function formatDuration(seconds: number | null | undefined): string {
	if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) {
		return '—'
	}

	if (seconds < 60) {
		return '<1 min'
	}

	const safeSeconds = Math.max(0, Math.floor(seconds))
	const hours = Math.floor(safeSeconds / 3600)
	const minutes = Math.floor((safeSeconds % 3600) / 60)
	const parts: string[] = []

	if (hours > 0) {
		parts.push(`${hours} h`)
	}

	if (minutes > 0) {
		parts.push(`${minutes} min`)
	}

	return parts.join(' ')
}

export function formatDifficulty(difficulty: number | null | undefined): string | null {
	if (difficulty === null || difficulty === undefined) {
		return null
	}

	return `${difficulty}/5`
}

export function formatStatus(status: FocusSessionStatus): string {
	const statuses: Record<FocusSessionStatus, string> = {
		active: 'In progress',
		completed: 'Completed',
		cancelled: 'Cancelled',
	}

	return statuses[status]
}
