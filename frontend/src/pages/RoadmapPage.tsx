import { Body, Button, Card, Skeleton, Title } from '../components/ui'

export function RoadmapPage() {
	const hasPlan = false

	const handleSetGoal = () => {
		// TODO: integrate Roadmap Agent (Sprint 3)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<Title>My roadmap</Title>

			{!hasPlan ? (
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
						<Body>Goal is not set</Body>
						<Button variant="primary" size="md" onClick={handleSetGoal}>
							Set goal
						</Button>
					</div>
				</Card>
			) : null}

			<Skeleton height={8} width="100%" borderRadius="var(--radius-full)" />

			<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
				{Array.from({ length: 4 }).map((_, index) => (
					<Card key={index}>
						<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
							<Skeleton height={16} width="50%" />
							<Skeleton height={12} width="72%" />
						</div>
					</Card>
				))}
			</div>
		</div>
	)
}
