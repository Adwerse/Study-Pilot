import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PomodoroScreen } from '../components/timer'
import { DailyNote } from '../components/today/DailyNote'
import { FocusBlockCard } from '../components/today/FocusBlockCard'
import { StageProgress } from '../components/today/StageProgress'
import { Body, Button, Caption, Card, Skeleton, Title } from '../components/ui'
import { useTodayPlan } from '../hooks/useTodayPlan'

const dateFormatter = new Intl.DateTimeFormat('en-US', {
	weekday: 'short',
	day: 'numeric',
	month: 'long',
})

export function TodayPage() {
	const navigate = useNavigate()
	const { plan, stage, loading, error, refetch, completedBlocks, markBlockDone } = useTodayPlan()
	const [activeBlockIndex, setActiveBlockIndex] = useState<number | null>(null)
	const [pomodoroCounts, setPomodoroCounts] = useState<Record<number, number>>({})
	const formattedDate = useMemo(() => dateFormatter.format(new Date()).replace(/\.$/, ''), [])

	if (loading) {
		return (
			<div style={{ padding: 'var(--space-4)', display: 'grid', gap: '12px' }}>
				<Skeleton height={72} />
				<Skeleton height={110} />
				<Skeleton height={110} />
				<Skeleton height={110} />
			</div>
		)
	}

	if (error) {
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
						<Body style={{ color: 'var(--tg-destructive)' }}>{error}</Body>
						<Button
							variant="secondary"
							size="md"
							onClick={() => {
								refetch()
							}}
						>
							Refresh
						</Button>
					</div>
				</Card>
			</div>
		)
	}

	if (!plan) {
		return (
			<div
				style={{
					padding: 'var(--space-4)',
					minHeight: '100%',
					display: 'grid',
					placeItems: 'center',
				}}
			>
				<div style={{ display: 'grid', gap: '8px', justifyItems: 'center', textAlign: 'center' }}>
					<Title>Start with a goal</Title>
					<Caption style={{ display: 'block' }}>Set a learning goal and I'll build today's plan</Caption>
					<Button variant="primary" size="md" onClick={() => navigate('/roadmap')}>
						Set goal
					</Button>
				</div>
			</div>
		)
	}

	const allBlocksCompleted = plan.blocks.length > 0 && completedBlocks.length === plan.blocks.length
	const activeBlock = activeBlockIndex !== null ? plan.blocks[activeBlockIndex] : null
	const getPomodoroCount = (blockIndex: number) => pomodoroCounts[blockIndex] ?? 1

	const handleSessionComplete = () => {
		if (activeBlockIndex !== null) {
			markBlockDone(activeBlockIndex)
		}

		setActiveBlockIndex(null)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<header style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
				<Title>Today</Title>
				<Caption style={{ marginTop: '4px' }}>{formattedDate}</Caption>
			</header>

			{stage ? (
				<StageProgress
					stage={stage}
					completedToday={completedBlocks.length}
					totalToday={plan.blocks.length}
				/>
			) : null}

			<DailyNote note={plan.daily_note} />

			<Caption
				style={{
					display: 'block',
					marginTop: '20px',
					fontWeight: 500,
					color: 'var(--tg-text)',
				}}
			>
				Focus blocks for today
			</Caption>

			<div style={{ display: 'grid', gap: '12px' }}>
				{plan.blocks.map((block, index) => {
					const blockIsDone = completedBlocks.includes(index)
					const blockIsActive = activeBlockIndex === index
					const isBlockedByAnotherSession = activeBlockIndex !== null && activeBlockIndex !== index

					return (
						<div key={`${block.topic}-${index}`} style={{ pointerEvents: isBlockedByAnotherSession ? 'none' : 'auto' }}>
							<FocusBlockCard
								block={block}
								index={index}
								isDone={blockIsDone}
								isActive={blockIsActive}
								pomodoroCount={getPomodoroCount(index)}
								onPomodoroCountChange={(count) => {
									setPomodoroCounts((previous) => ({ ...previous, [index]: count }))
								}}
								onStart={() => {
									setActiveBlockIndex(index)
								}}
								onMarkDone={() => {
									setActiveBlockIndex(index)
								}}
							/>
						</div>
					)
				})}
			</div>

			{allBlocksCompleted ? (
				<Card>
					<div
						style={{
							border: '1px solid var(--tg-success)',
							borderRadius: 'var(--radius-sm)',
							padding: '12px',
							display: 'grid',
							gap: '4px',
						}}
					>
						<Body>Great work! Today's plan is complete 🎯</Body>
						<Caption style={{ display: 'block' }}>Come back tomorrow for a new plan</Caption>
					</div>
				</Card>
			) : null}

			{activeBlockIndex !== null && activeBlock ? (
				<div
					style={{
						position: 'fixed',
						inset: 0,
						background: 'var(--tg-bg)',
						zIndex: 150,
						padding: '24px 16px',
						overflowY: 'auto',
					}}
				>
					<Button variant="ghost" size="sm" onClick={() => setActiveBlockIndex(null)}>
						← Back
					</Button>
					<div
						style={{
							maxWidth: '420px',
							margin: '24px auto 0',
							display: 'grid',
							placeItems: 'center',
						}}
					>
						<PomodoroScreen
							suggestedTopic={activeBlock.topic}
							stageId={stage?.id}
							pomodoroCount={getPomodoroCount(activeBlockIndex)}
							onSessionComplete={handleSessionComplete}
						/>
					</div>
				</div>
			) : null}
		</div>
	)
}
