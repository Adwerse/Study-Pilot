import { Caption, Card, Skeleton, Title } from '../components/ui'
import { useAnalytics } from '../hooks'

export function AnalyticsPage() {
	const { daily, loading } = useAnalytics()

	// TODO: integrate Analytics Agent (Sprint 6)
	const metrics = [
		{ label: 'Sessions', value: daily?.sessions_count ?? 0 },
		{ label: 'Minutes', value: daily?.total_minutes ?? 0 },
		{ label: 'Streak', value: daily?.streak_days ?? 0 },
	]

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<Title>Analytics</Title>

			<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 'var(--space-2)' }}>
				{metrics.map((metric) => (
					<Card key={metric.label} padding="sm">
						<div style={{ display: 'grid', gap: 'var(--space-1)' }}>
							{loading ? <Skeleton width="68%" height={20} /> : <strong>{metric.value}</strong>}
							<Caption>{metric.label}</Caption>
						</div>
					</Card>
				))}
			</div>

			<Skeleton height={160} borderRadius="12px" />
			<Caption>Activity over the week</Caption>
		</div>
	)
}
