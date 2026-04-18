import type { PlanStage } from '../types/api'
import { GeneratingState } from '../components/roadmap/GeneratingState'
import { GoalForm } from '../components/roadmap/GoalForm'
import { StageCard } from '../components/roadmap/StageCard'
import { Body, Button, Caption, Card, Divider, Title } from '../components/ui'
import { useRoadmap } from '../hooks/useRoadmap'

export function RoadmapPage() {
	const { state, plan, error, generate, reset } = useRoadmap()

	const stages = (plan?.stages ?? []) as Array<PlanStage & { topics?: string[]; hours_required?: number }>
	const currentWeekIndex = stages.findIndex((stage) => stage.status === 'in_progress')
	const totalHours = stages.reduce((sum, stage) => sum + (typeof stage.hours_required === 'number' ? stage.hours_required : 0), 0)

	if (state === 'generating') {
		return (
			<div style={{ padding: 'var(--space-4)' }}>
				<GeneratingState />
			</div>
		)
	}

	if (state === 'error') {
		return (
			<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
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
						<Body style={{ color: 'var(--tg-destructive)' }}>{error ?? 'Не удалось загрузить roadmap'}</Body>
						<Button variant="destructive" size="md" onClick={reset}>
							Попробовать снова
						</Button>
					</div>
				</Card>
			</div>
		)
	}

	if (state === 'empty') {
		return (
			<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
				<div>
					<Title>Поставь цель</Title>
					<Caption style={{ display: 'block', marginTop: '4px' }}>
						Расскажи что хочешь изучить - составлю план по неделям
					</Caption>
				</div>

				<div style={{ marginTop: '24px' }}>
					<GoalForm onSubmit={generate} loading={false} />
				</div>
			</div>
		)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
				<div>
					<Title style={{ marginBottom: '4px' }}>{plan?.title ?? 'Roadmap'}</Title>
					<Caption>
						{stages.length} недель · {totalHours} ч
					</Caption>
				</div>

				<Button variant="ghost" size="sm" onClick={reset}>
					Пересоздать
				</Button>
			</div>

			<Divider />

			<div style={{ display: 'grid', gap: '12px' }}>
				{stages.map((stage, index) => (
					<StageCard
						key={stage.id}
						stage={stage}
						index={index}
						isCurrentWeek={index === currentWeekIndex || (currentWeekIndex === -1 && index === 0)}
					/>
				))}
			</div>
		</div>
	)
}
