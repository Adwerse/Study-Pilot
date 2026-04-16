import { Button, Caption, Card, Skeleton, Subtitle, Title } from '../components/ui'
import { useTodayTasks } from '../hooks'

const weekdayFormatter = new Intl.DateTimeFormat('en-US', { weekday: 'long' })
const dateFormatter = new Intl.DateTimeFormat('en-US', { dateStyle: 'full' })

function toCapitalized(text: string): string {
	return text.charAt(0).toUpperCase() + text.slice(1)
}

export function TodayPage() {
	const { tasks, loading } = useTodayTasks()
	const now = new Date()
	const weekday = toCapitalized(weekdayFormatter.format(now))
	const fullDate = toCapitalized(dateFormatter.format(now))

	const handleStartSession = () => {
		// TODO: integrate Focus Agent (Sprint 4)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<header style={{ display: 'grid', gap: 'var(--space-1)' }}>
				<Title>Today, {weekday}</Title>
				<Caption>{fullDate}</Caption>
			</header>

			<section style={{ display: 'grid', gap: 'var(--space-3)' }}>
				<Subtitle>Focus blocks</Subtitle>
				{loading
					? Array.from({ length: 3 }).map((_, index) => (
							<Card key={`skeleton-${index}`}>
								<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
									<Skeleton height={18} width="55%" />
									<Skeleton lines={2} height={12} />
								</div>
							</Card>
						))
					: tasks.length > 0
						? tasks.map((task) => (
								<Card key={task.id}>
									<div style={{ display: 'grid', gap: 'var(--space-1)' }}>
										<Subtitle>{task.title}</Subtitle>
										<Caption>{task.deliverable}</Caption>
									</div>
								</Card>
							))
						: Array.from({ length: 3 }).map((_, index) => (
								<Card key={`fallback-${index}`}>
									<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
										<Skeleton height={18} width="55%" />
										<Skeleton lines={2} height={12} />
									</div>
								</Card>
							))}
			</section>

			<Button variant="primary" size="lg" fullWidth disabled onClick={handleStartSession}>
				Start session
			</Button>
		</div>
	)
}
