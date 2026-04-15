import { Caption, Card, Skeleton, Title } from '../components/ui'

export function AnalyticsPage() {
	// TODO: integrate Analytics Agent (Sprint 6)
	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<Title>Analytics</Title>

			<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 'var(--space-2)' }}>
				{[
					{ label: 'Sessions' },
					{ label: 'Minutes' },
					{ label: 'Streak' },
				].map((metric) => (
					<Card key={metric.label} padding="sm">
						<div style={{ display: 'grid', gap: 'var(--space-1)' }}>
							<Skeleton width="68%" height={20} />
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
