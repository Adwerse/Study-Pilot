import { CSSProperties, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFocusHistory } from '../hooks/useFocusHistory'
import type { FocusSession, FocusSessionStatus } from '../types/api'
import { formatDifficulty, formatDuration, formatSessionTimeRange, formatStatus } from '../utils/focusHistoryFormatters'
import { Badge, Body, Button, Caption, Card, Skeleton, Title } from '../components/ui'

const pageStyle: CSSProperties = {
	padding: 'var(--space-4)',
	display: 'grid',
	gap: 'var(--space-4)',
}

const toolbarStyle: CSSProperties = {
	display: 'grid',
	gap: '10px',
}

const dateControlsStyle: CSSProperties = {
	display: 'grid',
	gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
	gap: '8px',
}

const dateInputStyle: CSSProperties = {
	width: '100%',
	minHeight: '40px',
	border: '1px solid rgba(0, 0, 0, 0.08)',
	borderRadius: 'var(--radius-md)',
	background: 'var(--tg-secondary-bg)',
	color: 'var(--tg-text)',
	padding: '0 12px',
	font: 'inherit',
	colorScheme: 'light dark',
}

const selectedDateFormatter = new Intl.DateTimeFormat(undefined, {
	weekday: 'long',
	day: 'numeric',
	month: 'long',
})

function toDateInputValue(date: Date): string {
	const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
	return localDate.toISOString().slice(0, 10)
}

function getRelativeDateInputValue(daysFromToday: number): string {
	const date = new Date()
	date.setDate(date.getDate() + daysFromToday)
	return toDateInputValue(date)
}

function parseDateInputValue(value: string): Date {
	return new Date(`${value}T00:00:00`)
}

function getSelectedDateLabel(value: string): string {
	const date = parseDateInputValue(value)

	if (Number.isNaN(date.getTime())) {
		return value
	}

	return selectedDateFormatter.format(date)
}

function getStatusBadgeVariant(status: FocusSessionStatus): 'success' | 'danger' | 'info' {
	if (status === 'completed') {
		return 'success'
	}

	if (status === 'cancelled') {
		return 'danger'
	}

	return 'info'
}

function getSessionTitle(session: FocusSession): string {
	return session.topic?.trim() || 'No topic'
}

function getActualDurationSeconds(session: FocusSession, now: number): number | null {
	if (session.actual_duration_seconds !== null && session.actual_duration_seconds !== undefined) {
		return session.actual_duration_seconds
	}

	const startedAtMs = new Date(session.started_at).getTime()

	if (Number.isNaN(startedAtMs)) {
		return null
	}

	if (session.ended_at) {
		const endedAtMs = new Date(session.ended_at).getTime()

		if (!Number.isNaN(endedAtMs)) {
			return Math.max(0, Math.floor((endedAtMs - startedAtMs) / 1000))
		}
	}

	if (session.status === 'active') {
		return Math.max(0, Math.floor((now - startedAtMs) / 1000))
	}

	return null
}

function FocusHistorySkeleton() {
	return (
		<div style={{ display: 'grid', gap: '12px' }} aria-label="Loading focus history">
			<Skeleton height={88} />
			<Skeleton height={88} />
			<Skeleton height={88} />
		</div>
	)
}

function FocusSessionCard({ session, now }: { session: FocusSession; now: number }) {
	const difficulty = formatDifficulty(session.difficulty)
	const actualDurationSeconds = getActualDurationSeconds(session, now)
	const actualDuration = formatDuration(actualDurationSeconds)
	const plannedDuration = session.planned_duration_minutes
		? formatDuration(session.planned_duration_minutes * 60)
		: null
	const durationLabel = plannedDuration ? `${actualDuration} of ${plannedDuration}` : actualDuration
	const notes = session.notes?.trim()

	return (
		<Card padding="md">
			<article style={{ display: 'grid', gap: '10px', minWidth: 0 }}>
				<header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
					<Badge variant={getStatusBadgeVariant(session.status)}>{formatStatus(session.status)}</Badge>
					<Caption style={{ color: 'var(--tg-text)', fontWeight: 600, whiteSpace: 'nowrap' }}>{durationLabel}</Caption>
				</header>

				<div style={{ display: 'grid', gap: '4px', minWidth: 0 }}>
					<Body
						style={{
							fontWeight: 600,
							overflow: 'hidden',
							textOverflow: 'ellipsis',
							whiteSpace: 'nowrap',
						}}
					>
						{getSessionTitle(session)}
					</Body>
					<Caption>{formatSessionTimeRange(session.started_at, session.ended_at)}</Caption>
				</div>

				{difficulty || notes ? (
					<div style={{ display: 'grid', gap: '4px' }}>
						{difficulty ? <Caption style={{ color: 'var(--tg-text)' }}>Difficulty: {difficulty}</Caption> : null}
						{notes ? (
							<Caption
								style={{
									display: '-webkit-box',
									overflow: 'hidden',
									WebkitBoxOrient: 'vertical',
									WebkitLineClamp: 2,
									whiteSpace: 'pre-wrap',
								}}
							>
								{notes}
							</Caption>
						) : null}
					</div>
				) : null}
			</article>
		</Card>
	)
}

export function FocusHistoryScreen() {
	const navigate = useNavigate()
	const today = useMemo(() => getRelativeDateInputValue(0), [])
	const yesterday = useMemo(() => getRelativeDateInputValue(-1), [])
	const [selectedDate, setSelectedDate] = useState(today)
	const [now, setNow] = useState(() => Date.now())
	const { items, total, loading, loadingMore, error, hasMore, refetch, loadMore } = useFocusHistory({
		date: selectedDate,
		limit: 20,
		offset: 0,
	})
	const hasActiveSession = items.some((item) => item.status === 'active' && !item.ended_at)

	useEffect(() => {
		if (!hasActiveSession) {
			return
		}

		const intervalId = window.setInterval(() => {
			setNow(Date.now())
		}, 60_000)

		return () => {
			window.clearInterval(intervalId)
		}
	}, [hasActiveSession])

	return (
		<div style={pageStyle}>
			<header style={{ display: 'grid', gap: '12px' }}>
				<Button variant="ghost" size="sm" onClick={() => navigate('/today')}>
					← Today
				</Button>
				<div style={{ display: 'grid', gap: '4px' }}>
					<Title>Focus history</Title>
					<Caption style={{ textTransform: 'capitalize' }}>{getSelectedDateLabel(selectedDate)}</Caption>
				</div>
			</header>

			<section style={toolbarStyle}>
				<div style={dateControlsStyle}>
					<Button
						variant={selectedDate === today ? 'primary' : 'secondary'}
						size="md"
						onClick={() => setSelectedDate(today)}
					>
						Today
					</Button>
					<Button
						variant={selectedDate === yesterday ? 'primary' : 'secondary'}
						size="md"
						onClick={() => setSelectedDate(yesterday)}
					>
						Yesterday
					</Button>
				</div>
				<input
					aria-label="Choose date"
					type="date"
					value={selectedDate}
					onChange={(event) => {
						if (event.target.value) {
							setSelectedDate(event.target.value)
						}
					}}
					style={dateInputStyle}
				/>
			</section>

			{loading ? <FocusHistorySkeleton /> : null}

			{!loading && error ? (
				<Card>
					<div
						style={{
							border: '1px solid var(--tg-destructive)',
							borderRadius: 'var(--radius-sm)',
							padding: '12px',
							display: 'grid',
							gap: '12px',
						}}
					>
						<Body style={{ color: 'var(--tg-destructive)' }}>
							{error.status === 401 ? 'Could not verify your Telegram session.' : error.detail}
						</Body>
						<Button variant="secondary" size="md" onClick={refetch}>
							Retry
						</Button>
					</div>
				</Card>
			) : null}

			{!loading && !error && items.length === 0 ? (
				<Card>
					<div style={{ display: 'grid', gap: '6px', justifyItems: 'center', textAlign: 'center', padding: '12px 0' }}>
						<Body style={{ fontWeight: 600 }}>No sessions for this day</Body>
						<Caption>Start a Pomodoro from today's plan, and your history will appear here.</Caption>
					</div>
				</Card>
			) : null}

			{!loading && !error && items.length > 0 ? (
				<section style={{ display: 'grid', gap: '12px' }} aria-label="Focus sessions list">
					{items.map((session) => (
						<FocusSessionCard key={session.id} session={session} now={now} />
					))}
				</section>
			) : null}

			{!loading && !error && hasMore ? (
				<Button variant="secondary" size="md" fullWidth loading={loadingMore} onClick={loadMore}>
					Load more
				</Button>
			) : null}

			{!loading && !error && total > 0 ? (
				<Caption style={{ display: 'block', textAlign: 'center' }}>
					Showing {items.length} of {total}
				</Caption>
			) : null}
		</div>
	)
}

export const FocusHistoryPage = FocusHistoryScreen
