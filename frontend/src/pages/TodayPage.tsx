import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DailyNote } from '../components/today/DailyNote'
import { FocusBlockCard } from '../components/today/FocusBlockCard'
import { StageProgress } from '../components/today/StageProgress'
import { Body, Button, Caption, Card, Skeleton, Title } from '../components/ui'
import { useFocus } from '../hooks/useFocus'
import { useTodayPlan } from '../hooks/useTodayPlan'
import { normalizeApiError } from '../lib/api'

const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
	weekday: 'short',
	day: 'numeric',
	month: 'long',
})

export function TodayPage() {
	const navigate = useNavigate()
	const { plan, stage, loading, error, refetch, completedBlocks, markBlockDone } = useTodayPlan()
	const { session, isActive, start, end } = useFocus()
	const [activeBlockIndex, setActiveBlockIndex] = useState<number | null>(null)
	const [actionError, setActionError] = useState<string | null>(null)
	const formattedDate = useMemo(() => dateFormatter.format(new Date()).replace(/\.$/, ''), [])

	useEffect(() => {
		if (!session || !isActive) {
			setActiveBlockIndex(null)
		}
	}, [isActive, session])

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
								setActionError(null)
								refetch()
							}}
						>
							Обновить
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
					<Title>Начни с цели</Title>
					<Caption style={{ display: 'block' }}>Поставь учебную цель — составлю план на сегодня</Caption>
					<Button variant="primary" size="md" onClick={() => navigate('/roadmap')}>
						Поставить цель
					</Button>
				</div>
			</div>
		)
	}

	const allBlocksCompleted = plan.blocks.length > 0 && completedBlocks.length === plan.blocks.length

	const handleStart = async (blockIndex: number, topic: string) => {
		if (isActive && activeBlockIndex !== null && activeBlockIndex !== blockIndex) {
			return
		}

		setActionError(null)

		try {
			await start(topic, stage?.id)
			setActiveBlockIndex(blockIndex)
		} catch (startError) {
			setActionError(normalizeApiError(startError).detail)
		}
	}

	const handleMarkDone = async (blockIndex: number) => {
		setActionError(null)

		try {
			await end(3)
			markBlockDone(blockIndex)
			setActiveBlockIndex(null)
		} catch (endError) {
			setActionError(normalizeApiError(endError).detail)
		}
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<header style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
				<Title>Сегодня</Title>
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

			{actionError ? (
				<Card>
					<div
						style={{
							border: '1px solid var(--tg-destructive)',
							borderRadius: 'var(--radius-sm)',
							padding: '12px',
						}}
					>
						<Body style={{ color: 'var(--tg-destructive)' }}>{actionError}</Body>
					</div>
				</Card>
			) : null}

			<Caption
				style={{
					display: 'block',
					marginTop: '20px',
					fontWeight: 500,
					color: 'var(--tg-text)',
				}}
			>
				Фокус-блоки на день
			</Caption>

			<div style={{ display: 'grid', gap: '12px' }}>
				{plan.blocks.map((block, index) => {
					const blockIsDone = completedBlocks.includes(index)
					const blockIsActive = isActive && activeBlockIndex === index
					const isBlockedByAnotherSession = isActive && activeBlockIndex !== null && activeBlockIndex !== index

					return (
						<div key={`${block.topic}-${index}`} style={{ pointerEvents: isBlockedByAnotherSession ? 'none' : 'auto' }}>
							<FocusBlockCard
								block={block}
								index={index}
								isDone={blockIsDone}
								isActive={blockIsActive}
								onStart={async () => {
									await handleStart(index, block.topic)
								}}
								onMarkDone={async () => {
									await handleMarkDone(index)
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
						<Body>Отличная работа! План на сегодня выполнен 🎯</Body>
						<Caption style={{ display: 'block' }}>Возвращайся завтра за новым планом</Caption>
					</div>
				</Card>
			) : null}
		</div>
	)
}
