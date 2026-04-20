import type { PlanStage } from '../../types/api'
import { Badge, Caption, Card, Subtitle } from '../ui'

type StageProgressProps = {
	stage: PlanStage
	completedToday: number
	totalToday: number
}

function truncateDeliverable(deliverable: string): string {
	if (deliverable.length <= 80) {
		return deliverable
	}

	return `${deliverable.slice(0, 80)}...`
}

function getProgressWidth(completedToday: number, totalToday: number): string {
	if (totalToday <= 0) {
		return '0%'
	}

	const rawProgress = (completedToday / totalToday) * 100
	const safeProgress = Math.min(100, Math.max(0, rawProgress))

	return `${safeProgress}%`
}

export function StageProgress({ stage, completedToday, totalToday }: StageProgressProps) {
	return (
		<Card padding="sm">
			<div>
				<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
					<Caption style={{ color: 'var(--tg-text)' }}>Текущий этап</Caption>
					<Badge variant="info">Неделя {stage.week_number}</Badge>
				</div>

				<Subtitle style={{ marginTop: '4px' }}>{stage.title}</Subtitle>

				<Caption
					style={{
						display: 'block',
						marginTop: '2px',
						color: 'var(--tg-hint)',
					}}
				>
					{truncateDeliverable(stage.deliverable)}
				</Caption>

				<div
					style={{
						height: '6px',
						background: 'var(--tg-secondary-bg)',
						borderRadius: '3px',
						marginTop: '12px',
						overflow: 'hidden',
					}}
				>
					<div
						data-testid="progress-fill"
						style={{
							width: getProgressWidth(completedToday, totalToday),
							height: '100%',
							background: 'var(--tg-button)',
							borderRadius: '3px',
							transition: 'width 400ms ease-out',
						}}
					/>
				</div>

				<Caption
					style={{
						display: 'block',
						marginTop: '6px',
						color: 'var(--tg-hint)',
						textAlign: 'right',
					}}
				>
					{completedToday} из {totalToday} блоков сегодня
				</Caption>
			</div>
		</Card>
	)
}
