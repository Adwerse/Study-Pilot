import { useEffect, useState } from 'react'
import { usePomodoro } from '../../hooks/usePomodoro'
import { Body, Button, Caption, Skeleton, Title } from '../ui'
import { CircularTimer } from './CircularTimer'
import { DifficultyPicker } from './DifficultyPicker'
import { StartForm } from './StartForm'

type PomodoroScreenProps = {
	suggestedTopic?: string
	stageId?: string
	onSessionComplete?: () => void
}

const centeredStackStyle = {
	display: 'flex',
	flexDirection: 'column',
	alignItems: 'center',
	width: '100%',
} as const

export function PomodoroScreen({ suggestedTopic, stageId, onSessionComplete }: PomodoroScreenProps) {
	const { status, topic, remaining, progress, loading, error, start, stop } = usePomodoro()
	const [showPicker, setShowPicker] = useState(false)

	useEffect(() => {
		if (status !== 'running') {
			setShowPicker(false)
		}
	}, [status])

	const handleStop = async (difficulty: number) => {
		await stop(difficulty)
		setShowPicker(false)
		onSessionComplete?.()
	}

	if (loading && status === 'idle') {
		return (
			<div style={{ display: 'grid', placeItems: 'center', minHeight: '320px' }}>
				<Skeleton height={220} width={220} borderRadius="50%" />
			</div>
		)
	}

	if (status === 'idle') {
		return (
			<div style={{ width: '100%', display: 'grid', gap: '16px' }}>
				<StartForm
					onStart={(nextTopic) => start(nextTopic, stageId)}
					loading={loading}
					suggestedTopic={suggestedTopic}
				/>
				{error ? <Body style={{ color: 'var(--tg-destructive)' }}>{error}</Body> : null}
			</div>
		)
	}

	if (status === 'finished') {
		return (
			<div style={{ ...centeredStackStyle, gap: '24px', textAlign: 'center' }}>
				<CircularTimer remaining={remaining} progress={progress} status={status} />
				<div style={{ display: 'grid', gap: '8px' }}>
					<Title>Session complete 🎯</Title>
					<Caption>Rate how difficult it felt</Caption>
				</div>
				{error ? <Body style={{ color: 'var(--tg-destructive)' }}>{error}</Body> : null}
				<DifficultyPicker onSelect={handleStop} loading={loading} />
			</div>
		)
	}

	return (
		<div style={{ ...centeredStackStyle, gap: '32px', textAlign: 'center' }}>
			<CircularTimer remaining={remaining} progress={progress} status={status} />
			<Caption style={{ color: 'var(--tg-text)', fontWeight: 500 }}>{topic}</Caption>
			<div style={{ display: 'grid', gap: '10px', justifyItems: 'center' }}>
				<Button variant="ghost" size="sm" onClick={() => setShowPicker(true)}>
					Stop
				</Button>
				{error ? <Body style={{ color: 'var(--tg-destructive)' }}>{error}</Body> : null}
			</div>
			{showPicker ? <DifficultyPicker onSelect={handleStop} loading={loading} /> : null}
		</div>
	)
}
