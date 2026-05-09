import { Caption, Card, Subtitle } from '../ui'
import type { DailyBreakdownItem } from '../../types/api'
import { formatMinutes } from '../../utils/analyticsFormatters'
import { buildWeeklyBreakdownSlots, type WeeklyBreakdownSlot } from './weeklySlots'

type ChartValueKey = 'focusMinutes' | 'sessionsCount'

interface WeeklyBarChartProps {
	title: string
	dailyBreakdown: DailyBreakdownItem[]
	weekStart?: string
	valueKey: ChartValueKey
	ariaLabel: string
	formatValue: (value: number) => string
}

export interface WeeklyChartProps {
	dailyBreakdown: DailyBreakdownItem[]
	weekStart?: string
}

function getBarHeight(value: number, maxValue: number): string {
	if (maxValue <= 0 || value <= 0) {
		return '6px'
	}

	return `${Math.max(8, Math.round((value / maxValue) * 100))}%`
}

function getSlotValue(slot: WeeklyBreakdownSlot, valueKey: ChartValueKey): number {
	return valueKey === 'focusMinutes' ? slot.focusMinutes : slot.sessionsCount
}

function WeeklyBarChart({
	title,
	dailyBreakdown,
	weekStart,
	valueKey,
	ariaLabel,
	formatValue,
}: WeeklyBarChartProps) {
	const slots = buildWeeklyBreakdownSlots(dailyBreakdown, weekStart)
	const maxValue = Math.max(0, ...slots.map((slot) => getSlotValue(slot, valueKey)))

	return (
		<Card>
			<section className="analytics-chart-card" aria-label={ariaLabel}>
				<Subtitle>{title}</Subtitle>
				<div className="analytics-bar-chart">
					{slots.map((slot) => {
						const value = getSlotValue(slot, valueKey)
						const valueLabel = formatValue(value)

						return (
							<div className="analytics-bar-column" key={`${slot.date || slot.label}-${valueKey}`}>
								<div
									className="analytics-bar-track"
									title={`${slot.date || slot.label}: ${valueLabel}`}
									aria-label={`${slot.label}: ${valueLabel}`}
								>
									<div
										className={value > 0 ? 'analytics-bar' : 'analytics-bar analytics-bar-empty'}
										style={{ height: getBarHeight(value, maxValue) }}
									/>
								</div>
								<Caption>{slot.label}</Caption>
							</div>
						)
					})}
				</div>
			</section>
		</Card>
	)
}

export function WeeklyFocusChart({ dailyBreakdown, weekStart }: WeeklyChartProps) {
	return (
		<WeeklyBarChart
			title="Фокус по дням"
			dailyBreakdown={dailyBreakdown}
			weekStart={weekStart}
			valueKey="focusMinutes"
			ariaLabel="График минут фокуса по дням"
			formatValue={formatMinutes}
		/>
	)
}

export function WeeklySessionsChart({ dailyBreakdown, weekStart }: WeeklyChartProps) {
	return (
		<WeeklyBarChart
			title="Сессии по дням"
			dailyBreakdown={dailyBreakdown}
			weekStart={weekStart}
			valueKey="sessionsCount"
			ariaLabel="График количества сессий по дням"
			formatValue={(value) => String(value)}
		/>
	)
}
