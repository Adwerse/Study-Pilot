const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatMinutes(minutes: number | null | undefined): string {
	const safeMinutes = Number.isFinite(minutes) ? Math.max(0, Math.round(minutes ?? 0)) : 0
	const hours = Math.floor(safeMinutes / 60)
	const remainingMinutes = safeMinutes % 60

	if (hours === 0) {
		return `${remainingMinutes}м`
	}

	if (remainingMinutes === 0) {
		return `${hours}ч`
	}

	return `${hours}ч ${remainingMinutes}м`
}

export function formatPercent(value: number | null | undefined): string {
	if (value === null || value === undefined || !Number.isFinite(value)) {
		return '—'
	}

	return `${Math.round(value)}%`
}

export function formatStreak(days: number | null | undefined): string {
	const safeDays = Number.isFinite(days) ? Math.max(0, Math.round(days ?? 0)) : 0
	const mod10 = safeDays % 10
	const mod100 = safeDays % 100

	if (mod10 === 1 && mod100 !== 11) {
		return `${safeDays} день`
	}

	if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
		return `${safeDays} дня`
	}

	return `${safeDays} дней`
}

export function toLocalDateString(date: Date): string {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')

	return `${year}-${month}-${day}`
}

export function toApiDate(date: Date): string {
	return toLocalDateString(date)
}

export function parseLocalDateString(value: string): Date {
	const match = DATE_PATTERN.exec(value)

	if (!match) {
		return new Date(Number.NaN)
	}

	const [, year, month, day] = match
	return new Date(Number(year), Number(month) - 1, Number(day))
}

export function getTodayDateString(now = new Date()): string {
	return toLocalDateString(now)
}

export function getYesterdayDateString(now = new Date()): string {
	return shiftDate(getTodayDateString(now), -1)
}

export function shiftDate(date: string, days: number): string {
	const parsedDate = parseLocalDateString(date)

	if (Number.isNaN(parsedDate.getTime())) {
		return date
	}

	parsedDate.setDate(parsedDate.getDate() + days)
	return toLocalDateString(parsedDate)
}

export function getWeekStart(date: string | Date = new Date()): string {
	const parsedDate = typeof date === 'string' ? parseLocalDateString(date) : new Date(date.getTime())

	if (Number.isNaN(parsedDate.getTime())) {
		return typeof date === 'string' ? date : getTodayDateString()
	}

	const day = parsedDate.getDay()
	const offsetToMonday = day === 0 ? -6 : 1 - day
	parsedDate.setDate(parsedDate.getDate() + offsetToMonday)
	return toLocalDateString(parsedDate)
}

export function shiftWeek(weekStart: string, weeks: number): string {
	return shiftDate(weekStart, weeks * 7)
}

export function isFutureDate(date: string, today = getTodayDateString()): boolean {
	return parseLocalDateString(date).getTime() > parseLocalDateString(today).getTime()
}

export function isFutureWeek(weekStart: string, today = getTodayDateString()): boolean {
	return parseLocalDateString(getWeekStart(weekStart)).getTime() > parseLocalDateString(getWeekStart(today)).getTime()
}
