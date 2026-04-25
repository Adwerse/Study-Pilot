import { useEffect, useState } from 'react'
import { usePomodoro } from '../../hooks/usePomodoro'
import { Body, Button, Caption, Skeleton, Title } from '../ui'
import { CircularTimer } from './CircularTimer'
import { DifficultyPicker } from './DifficultyPicker'
import { StartForm } from './StartForm'

type PomodoroScreenProps = {
	suggestedTopic?: string
	stageId?: string
	pomodoroCount?: number
	onSessionComplete?: () => void
}

const centeredStackStyle = {
	display: 'flex',
	flexDirection: 'column',
	alignItems: 'center',
	width: '100%',
} as const

export function PomodoroScreen({ suggestedTopic, stageId, pomodoroCount = 1, onSessionComplete }: PomodoroScreenProps) {
	const {
		status,
		topic,
		pomodoroCount: activePomodoroCount,
		remaining,
		progress,
		loading,
		error,
		start,
		pause,
		resume,
		stop,
	} = usePomodoro(pomodoroCount)
	const [showPicker, setShowPicker] = useState(false)

	useEffect(() => {
		if (status !== 'running' && status !== 'paused') {
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
					onStart={(nextTopic) => start(nextTopic, stageId, pomodoroCount)}
					loading={loading}
					suggestedTopic={suggestedTopic}
					pomodoroCount={activePomodoroCount}
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
			<div style={{ display: 'grid', gap: '6px' }}>
				<Caption style={{ color: 'var(--tg-text)', fontWeight: 500 }}>{topic}</Caption>
				<Caption>
					{activePomodoroCount} pomodoro{activePomodoroCount === 1 ? '' : 's'}
				</Caption>
			</div>
			<div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
				<Button variant="secondary" size="sm" onClick={status === 'paused' ? resume : pause}>
					{status === 'paused' ? 'Resume' : 'Pause'}
				</Button>
				<Button variant="ghost" size="sm" onClick={() => setShowPicker(true)}>
					Stop
				</Button>
				{error ? <Body style={{ color: 'var(--tg-destructive)' }}>{error}</Body> : null}
			</div>
			{showPicker ? <DifficultyPicker onSelect={handleStop} loading={loading} /> : null}
		</div>
	)
}
