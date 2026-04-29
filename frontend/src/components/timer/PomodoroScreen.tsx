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

const timerShellStyle = {
	position: 'relative',
	width: 'clamp(220px, 72vw, 272px)',
	aspectRatio: '1',
	display: 'grid',
	placeItems: 'center',
	isolation: 'isolate',
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
	const timerShellClassName = `pomodoro-timer-shell${status === 'running' ? ' pomodoro-timer-shell--running' : ''}`

	const timerStyles = (
		<style>
			{`
				.pomodoro-timer-shell::before,
				.pomodoro-timer-shell::after {
					content: '';
					position: absolute;
					inset: 0;
					border-radius: 50%;
					opacity: 0;
					pointer-events: none;
					z-index: -1;
				}

				.pomodoro-timer-shell::before {
					background: conic-gradient(
						from 90deg,
						var(--tg-button),
						var(--tg-success),
						var(--tg-warning),
						var(--tg-button)
					);
					filter: blur(18px);
					transform: scale(0.9);
				}

				.pomodoro-timer-shell::after {
					inset: 18px;
					background: radial-gradient(
						circle,
						rgba(59, 130, 246, 0.16),
						transparent 68%
					);
				}

				.pomodoro-timer-shell--running::before {
					animation: pomodoro-gradient-spin 8s linear infinite, pomodoro-gradient-breathe 2.8s ease-in-out infinite;
					opacity: 0.72;
				}

				.pomodoro-timer-shell--running::after {
					animation: pomodoro-gradient-pulse 2.8s ease-in-out infinite;
					opacity: 1;
				}

				@keyframes pomodoro-gradient-spin {
					to {
						transform: scale(0.9) rotate(360deg);
					}
				}

				@keyframes pomodoro-gradient-breathe {
					0%, 100% {
						filter: blur(18px);
					}
					50% {
						filter: blur(24px);
					}
				}

				@keyframes pomodoro-gradient-pulse {
					0%, 100% {
						transform: scale(0.94);
					}
					50% {
						transform: scale(1.02);
					}
				}

				@media (prefers-reduced-motion: reduce) {
					.pomodoro-timer-shell--running::before,
					.pomodoro-timer-shell--running::after {
						animation: none;
					}
				}
			`}
		</style>
	)

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
				{timerStyles}
				<div className={timerShellClassName} style={timerShellStyle}>
					<CircularTimer remaining={remaining} progress={progress} status={status} />
				</div>
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
			{timerStyles}
			<div className={timerShellClassName} style={timerShellStyle}>
				<CircularTimer remaining={remaining} progress={progress} status={status} />
			</div>
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
