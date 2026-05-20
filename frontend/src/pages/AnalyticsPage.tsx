import { CSSProperties, ReactNode, useMemo, useState } from 'react'
import { ActivityHeatmap, TopicProgressList, WeeklyFocusChart, WeeklySessionsChart } from '../components/analytics'
import { Badge, Body, Button, Caption, Card, Skeleton, Subtitle, Title } from '../components/ui'
import { useDailyAnalytics, useWeeklyAnalytics } from '../hooks/useAnalytics'
import type {
	AnalyticsDataQuality,
	AnalyticsMetrics,
	AnalyticsReportResponse,
	ApiError,
	DailyBreakdownItem,
} from '../types/api'
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
} from '../utils/analyticsFormatters'
import '../styles/analytics.css'

type AnalyticsTab = 'daily' | 'weekly'

const periodDateFormatter = new Intl.DateTimeFormat('en-US', {
	day: 'numeric',
	month: 'short',
})

const fullDateFormatter = new Intl.DateTimeFormat('en-US', {
	weekday: 'long',
	day: 'numeric',
	month: 'long',
})

const iconButtonStyle: CSSProperties = {
	fontSize: '22px',
	lineHeight: 1,
}

function getBrowserTimezone(): string | undefined {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone
	} catch {
		return undefined
	}
}

function parseLocalDate(date: string): Date {
	const [year, month, day] = date.split('-').map(Number)
	return new Date(year, month - 1, day)
}

function formatDayPeriod(date: string, today: string): string {
	if (date === today) {
		return `Today, ${periodDateFormatter.format(parseLocalDate(date))}`
	}

	if (date === getYesterdayDateString(parseLocalDate(today))) {
		return `Yesterday, ${periodDateFormatter.format(parseLocalDate(date))}`
	}

	return fullDateFormatter.format(parseLocalDate(date))
}

function formatWeekPeriod(weekStart: string): string {
	const weekEnd = shiftDate(weekStart, 6)
	return `${periodDateFormatter.format(parseLocalDate(weekStart))} - ${periodDateFormatter.format(parseLocalDate(weekEnd))}`
}

function getDataQualityLabel(quality: AnalyticsDataQuality): string {
	const labels: Record<AnalyticsDataQuality, string> = {
		low: 'Limited data',
		medium: 'Enough data',
		high: 'Strong history',
	}

	return labels[quality]
}

function getDataQualityVariant(quality: AnalyticsDataQuality): 'success' | 'warning' | 'info' {
	if (quality === 'high') {
		return 'success'
	}

	if (quality === 'low') {
		return 'warning'
	}

	return 'info'
}

function getAnalyticsErrorMessage(error: ApiError | null): string {
	if (!error) {
		return 'Unable to load analytics'
	}

	if (error.status === 401) {
		return 'Open the Mini App through Telegram and try again.'
	}

	if (error.status === 503 || error.status === 500) {
		return 'The analytics service is temporarily unavailable.'
	}

	if (error.detail.toLowerCase().includes('network')) {
		return 'Check your connection and try again.'
	}

	return 'Try the request again in a moment.'
}

function isEmptyReport(metrics: AnalyticsMetrics | null | undefined): boolean {
	return (metrics?.total_focus_minutes ?? 0) === 0 && (metrics?.sessions_count ?? 0) === 0
}

function buildDailyBreakdown(date: string, metrics: AnalyticsMetrics | null | undefined): DailyBreakdownItem[] {
	return [
		{
			date,
			focus_minutes: metrics?.total_focus_minutes ?? 0,
			sessions_count: metrics?.sessions_count ?? 0,
			completion_rate: metrics?.completion_rate ?? null,
		},
	]
}

function IconButton({
	label,
	disabled,
	onClick,
	children,
}: {
	label: string
	disabled?: boolean
	onClick: () => void
	children: ReactNode
}) {
	return (
		<button
			type="button"
			aria-label={label}
			className="analytics-icon-button"
			disabled={disabled}
			onClick={onClick}
			style={iconButtonStyle}
		>
			{children}
		</button>
	)
}

function PeriodSwitch({
	activeTab,
	onChange,
}: {
	activeTab: AnalyticsTab
	onChange: (tab: AnalyticsTab) => void
}) {
	const tabs: Array<{ id: AnalyticsTab; label: string }> = [
		{ id: 'daily', label: 'Day' },
		{ id: 'weekly', label: 'Week' },
	]

	return (
		<div className="analytics-segment" role="tablist" aria-label="Analytics period">
			{tabs.map((tab) => {
				const active = activeTab === tab.id

				return (
					<button
						key={tab.id}
						type="button"
						role="tab"
						aria-selected={active}
						className={active ? 'analytics-segment-button analytics-segment-button-active' : 'analytics-segment-button'}
						onClick={() => onChange(tab.id)}
					>
						{tab.label}
					</button>
				)
			})}
		</div>
	)
}

function SummaryCard({
	label,
	value,
	loading,
}: {
	label: string
	value: string
	loading: boolean
}) {
	return (
		<Card padding="sm">
			<div style={{ display: 'grid', gap: '4px', minWidth: 0 }}>
				{loading ? <Skeleton width="72%" height={22} /> : <strong style={{ fontSize: 'var(--text-lg)' }}>{value}</strong>}
				<Caption>{label}</Caption>
			</div>
		</Card>
	)
}

function SummaryCards({
	metrics,
	loading,
}: {
	metrics: AnalyticsMetrics | null | undefined
	loading: boolean
}) {
	const cards = [
		{ label: 'Focus', value: formatMinutes(metrics?.total_focus_minutes ?? 0) },
		{ label: 'Sessions', value: String(metrics?.sessions_count ?? 0) },
		{ label: 'Streak', value: formatStreak(metrics?.streak_days ?? 0) },
		{ label: 'Completion', value: formatPercent(metrics?.completion_rate ?? null) },
	]

	return (
		<section className="analytics-summary-grid" aria-label="Key metrics">
			{cards.map((card) => (
				<SummaryCard key={card.label} label={card.label} value={card.value} loading={loading} />
			))}
		</section>
	)
}

function BestFocusHours({ hours }: { hours: string[] }) {
	return (
		<Card>
			<section className="analytics-section" aria-label="Best hours">
				<Subtitle>Best hours</Subtitle>
				{hours.length > 0 ? (
					<div className="analytics-chip-row">
						{hours.map((hour) => (
							<span className="analytics-chip" key={hour}>
								{hour}
							</span>
						))}
					</div>
				) : (
					<Caption>Not enough data yet</Caption>
				)}
			</section>
		</Card>
	)
}

function AiSummary({ report }: { report: AnalyticsReportResponse | null }) {
	const summary = report?.summary.trim() || 'Not enough data for a report yet.'
	const recommendations = report?.recommendations.filter((item) => item.trim().length > 0) ?? []
	const quality = report?.data_quality ?? 'low'

	return (
		<Card>
			<section className="analytics-section" aria-label="AI report and recommendations">
				<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
					<Subtitle>Report</Subtitle>
					<Badge variant={getDataQualityVariant(quality)}>{getDataQualityLabel(quality)}</Badge>
				</div>

				<Body>{summary}</Body>

				{recommendations.length > 0 ? (
					<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
						<Caption style={{ color: 'var(--tg-text)', fontWeight: 700 }}>Recommendations</Caption>
						<ul style={{ display: 'grid', gap: 'var(--space-2)', paddingLeft: '18px' }}>
							{recommendations.map((recommendation) => (
								<li key={recommendation}>
									<Body style={{ fontSize: 'var(--text-sm)' }}>{recommendation}</Body>
								</li>
							))}
						</ul>
					</div>
				) : null}
			</section>
		</Card>
	)
}

function AnalyticsLoadingState() {
	return (
		<div aria-label="Loading analytics" className="analytics-section">
			<Skeleton height={140} borderRadius="12px" />
			<Skeleton height={140} borderRadius="12px" />
			<Skeleton height={104} borderRadius="12px" />
		</div>
	)
}

function AnalyticsErrorState({ error, onRetry }: { error: ApiError | null; onRetry: () => void }) {
	return (
		<Card>
			<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
				<div style={{ display: 'grid', gap: '4px' }}>
					<Subtitle>Unable to load analytics</Subtitle>
					<Caption>{getAnalyticsErrorMessage(error)}</Caption>
				</div>
				<Button variant="secondary" size="md" onClick={onRetry}>
					Retry
				</Button>
			</div>
		</Card>
	)
}

function EmptyState({ activeTab }: { activeTab: AnalyticsTab }) {
	return (
		<Card>
			<div className="analytics-empty-card">
				<Body style={{ fontWeight: 600 }}>
					{activeTab === 'daily'
						? 'No focus sessions today yet. Start one short block and the charts will wake up.'
						: 'No data this week yet. Start with 25 minutes of focus.'}
				</Body>
			</div>
		</Card>
	)
}

export function AnalyticsPage() {
	const today = useMemo(() => getTodayDateString(), [])
	const currentWeekStart = useMemo(() => getWeekStart(today), [today])
	const yesterday = useMemo(() => getYesterdayDateString(parseLocalDate(today)), [today])
	const timezone = useMemo(() => getBrowserTimezone(), [])
	const [activeTab, setActiveTab] = useState<AnalyticsTab>('daily')
	const [selectedDate, setSelectedDate] = useState(today)
	const [selectedWeekStart, setSelectedWeekStart] = useState(currentWeekStart)

	const dailyState = useDailyAnalytics({ date: selectedDate, timezone, enabled: activeTab === 'daily' })
	const weeklyState = useWeeklyAnalytics({ weekStart: selectedWeekStart, timezone, enabled: activeTab === 'weekly' })
	const activeState = activeTab === 'daily' ? dailyState : weeklyState
	const activeReport = activeState.data
	const activeMetrics = activeReport?.metrics
	const activeLoading = activeState.isLoading
	const weeklyBreakdown = weeklyState.data?.daily_breakdown ?? []
	const heatmapBreakdown =
		activeTab === 'weekly' ? weeklyBreakdown : buildDailyBreakdown(selectedDate, activeMetrics)
	const periodLabel =
		activeTab === 'daily' ? formatDayPeriod(selectedDate, today) : formatWeekPeriod(selectedWeekStart)
	const nextDate = shiftDate(selectedDate, 1)
	const nextWeekStart = shiftWeek(selectedWeekStart, 1)
	const canMoveNextDay = !isFutureDate(nextDate, today)
	const canMoveNextWeek = !isFutureWeek(nextWeekStart, today)

	const selectDate = (date: string) => {
		if (isFutureDate(date, today)) {
			return
		}

		setSelectedDate(date)
		setSelectedWeekStart(getWeekStart(date))
	}

	const selectWeek = (weekStart: string) => {
		if (isFutureWeek(weekStart, today)) {
			return
		}

		setSelectedWeekStart(weekStart)
	}

	return (
		<div className="analytics-screen">
			<header className="analytics-header">
				<div style={{ display: 'grid', gap: '4px', minWidth: 0 }}>
					<Title>Analytics</Title>
					<Caption style={{ textTransform: 'capitalize' }}>{periodLabel}</Caption>
				</div>
			</header>

			<PeriodSwitch activeTab={activeTab} onChange={setActiveTab} />

			{activeTab === 'daily' ? (
				<div className="analytics-period-nav" aria-label="Day navigation">
					<IconButton label="Previous day" onClick={() => selectDate(shiftDate(selectedDate, -1))}>
						‹
					</IconButton>
					<Button variant={selectedDate === today ? 'primary' : 'secondary'} size="md" onClick={() => selectDate(today)}>
						Today
					</Button>
					<Button
						variant={selectedDate === yesterday ? 'primary' : 'secondary'}
						size="md"
						onClick={() => selectDate(yesterday)}
					>
						Yesterday
					</Button>
					<IconButton label="Next day" disabled={!canMoveNextDay} onClick={() => selectDate(nextDate)}>
						›
					</IconButton>
				</div>
			) : (
				<div className="analytics-period-nav" aria-label="Week navigation">
					<IconButton label="Previous week" onClick={() => selectWeek(shiftWeek(selectedWeekStart, -1))}>
						‹
					</IconButton>
					<Button
						variant={selectedWeekStart === currentWeekStart ? 'primary' : 'secondary'}
						size="md"
						onClick={() => selectWeek(currentWeekStart)}
					>
						Current week
					</Button>
					<Button
						variant={selectedWeekStart === shiftWeek(currentWeekStart, -1) ? 'primary' : 'secondary'}
						size="md"
						onClick={() => selectWeek(shiftWeek(currentWeekStart, -1))}
					>
						Previous week
					</Button>
					<IconButton label="Next week" disabled={!canMoveNextWeek} onClick={() => selectWeek(nextWeekStart)}>
						›
					</IconButton>
				</div>
			)}

			<SummaryCards metrics={activeMetrics} loading={activeLoading} />

			{activeLoading ? <AnalyticsLoadingState /> : null}

			{!activeLoading && activeState.error ? (
				<AnalyticsErrorState error={activeState.error} onRetry={activeState.refetch} />
			) : null}

			{!activeLoading && !activeState.error ? (
				<>
					{isEmptyReport(activeMetrics) ? <EmptyState activeTab={activeTab} /> : null}

					{activeTab === 'weekly' ? (
						<section className="analytics-section" aria-label="Weekly charts">
							<WeeklyFocusChart dailyBreakdown={weeklyBreakdown} weekStart={selectedWeekStart} />
							<WeeklySessionsChart dailyBreakdown={weeklyBreakdown} weekStart={selectedWeekStart} />
						</section>
					) : null}

					<ActivityHeatmap dailyBreakdown={heatmapBreakdown} weekStart={selectedWeekStart} />
					<TopicProgressList topics={activeMetrics?.most_focused_topics ?? []} />
					<BestFocusHours hours={activeMetrics?.best_focus_hours ?? []} />
					<AiSummary report={activeReport} />
				</>
			) : null}
		</div>
	)
}
