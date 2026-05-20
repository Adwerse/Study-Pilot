import { useMemo, useState } from 'react'
import { Body, Caption, Card, Subtitle } from '../ui'
import type { DailyBreakdownItem } from '../../types/api'
import { formatMinutes } from '../../utils/analyticsFormatters'
import { buildWeeklyBreakdownSlots, type WeeklyBreakdownSlot } from './weeklySlots'

export interface ActivityHeatmapProps {
	dailyBreakdown: DailyBreakdownItem[]
	weekStart?: string
}

function getHeatClass(minutes: number): string {
	if (minutes <= 0) {
		return 'heat-empty'
	}

	if (minutes <= 30) {
		return 'heat-low'
	}

	if (minutes <= 90) {
		return 'heat-medium'
	}

	return 'heat-high'
}

function getSlotDetails(slot: WeeklyBreakdownSlot): string {
	const date = slot.date || slot.label
	return `${date}: ${formatMinutes(slot.focusMinutes)}, ${slot.sessionsCount} sessions`
}

export function ActivityHeatmap({ dailyBreakdown, weekStart }: ActivityHeatmapProps) {
	const slots = useMemo(() => buildWeeklyBreakdownSlots(dailyBreakdown, weekStart), [dailyBreakdown, weekStart])
	const [selectedSlot, setSelectedSlot] = useState<WeeklyBreakdownSlot | null>(null)
	const detailsSlot = selectedSlot ?? slots.find((slot) => slot.focusMinutes > 0) ?? slots[0]

	return (
		<Card>
			<section className="analytics-section" aria-label="Activity heatmap">
				<div style={{ display: 'grid', gap: '4px' }}>
					<Subtitle>Activity</Subtitle>
					<Caption>7 days in the current period</Caption>
				</div>

				<div className="analytics-heatmap-grid">
					{slots.map((slot) => (
						<button
							key={slot.date || slot.label}
							type="button"
							className={`analytics-heat-cell ${getHeatClass(slot.focusMinutes)}`}
							title={getSlotDetails(slot)}
							aria-label={getSlotDetails(slot)}
							onClick={() => setSelectedSlot(slot)}
						>
							<Caption style={{ color: 'var(--tg-text)', fontWeight: 700 }}>{slot.label}</Caption>
						</button>
					))}
				</div>

				{detailsSlot ? (
					<Body style={{ fontSize: 'var(--text-sm)' }}>
						{detailsSlot.date || detailsSlot.label}: {formatMinutes(detailsSlot.focusMinutes)}, {detailsSlot.sessionsCount} sessions
					</Body>
				) : null}
			</section>
		</Card>
	)
}
