import { Body, Button, Card, Skeleton, Title } from '../components/ui'
import { usePlan } from '../hooks'

export function RoadmapPage() {
	const { plan, loading } = usePlan()
	const hasPlan = Boolean(plan)

	const handleSetGoal = () => {
		// TODO: integrate Roadmap Agent (Sprint 3)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<Title>My roadmap</Title>

			{loading ? (
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
						<Skeleton height={16} width="55%" />
						<Skeleton height={14} width="40%" />
					</div>
				</Card>
			) : !hasPlan ? (
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
						<Body>Goal is not set</Body>
						<Button variant="primary" size="md" onClick={handleSetGoal}>
							Set goal
						</Button>
					</div>
				</Card>
			) : (
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
						<Body>{plan?.title}</Body>
						<Body>{`${plan?.stages?.length ?? 0} stages`}</Body>
					</div>
				</Card>
			)}

			<Skeleton height={8} width="100%" borderRadius="var(--radius-full)" />

			<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
				{loading || !plan?.stages?.length
					? Array.from({ length: 4 }).map((_, index) => (
							<Card key={`stage-skeleton-${index}`}>
								<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
									<Skeleton height={16} width="50%" />
									<Skeleton height={12} width="72%" />
								</div>
							</Card>
						))
					: plan.stages.map((stage) => (
							<Card key={stage.id}>
								<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
									<Body>{stage.title}</Body>
									<Body>{stage.deliverable}</Body>
								</div>
							</Card>
						))}
			</div>
		</div>
	)
}
