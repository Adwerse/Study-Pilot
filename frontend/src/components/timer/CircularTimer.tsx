import { useId } from 'react'

type CircularTimerStatus = 'idle' | 'running' | 'paused' | 'finished'

export type CircularTimerProps = {
	remaining: number
	progress: number
	status: CircularTimerStatus
	size?: number
}

function formatTime(totalSeconds: number): string {
	const safeSeconds = Math.max(0, Math.floor(totalSeconds))
	const minutes = String(Math.floor(safeSeconds / 60)).padStart(2, '0')
	const seconds = String(safeSeconds % 60).padStart(2, '0')

	return `${minutes}:${seconds}`
}

function getCaption(status: CircularTimerStatus): string {
	if (status === 'running') {
		return 'remaining'
	}

	if (status === 'paused') {
		return 'paused'
	}

	if (status === 'finished') {
		return 'done!'
	}

	return 'ready'
}

export function CircularTimer({ remaining, progress, status, size = 220 }: CircularTimerProps) {
	const gradientId = `circular-timer-gradient-${useId().replace(/:/g, '')}`
	const radius = (size - 20) / 2
	const circumference = 2 * Math.PI * radius
	const safeProgress = Math.min(1, Math.max(0, progress))
	const strokeDashoffset = circumference * (1 - safeProgress)
	const center = size / 2
	const caption = getCaption(status)
	const progressStroke =
		status === 'running'
			? `url(#${gradientId})`
			: status === 'finished'
				? 'var(--tg-success)'
				: status === 'paused'
					? 'var(--tg-hint)'
					: 'var(--tg-button)'

	return (
		<svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={formatTime(remaining)}>
			<style>
				{`
					.circular-timer__progress {
						filter: drop-shadow(0 0 0 rgba(59, 130, 246, 0));
						transition: stroke-dashoffset 1s linear, stroke 0.3s ease, filter 0.3s ease;
					}

					.circular-timer__progress--running {
						filter: drop-shadow(0 0 14px rgba(59, 130, 246, 0.38));
					}

					.circular-timer__gradient-stop-a {
						animation: circular-timer-gradient-a 4s ease-in-out infinite;
					}

					.circular-timer__gradient-stop-b {
						animation: circular-timer-gradient-b 4s ease-in-out infinite;
					}

					.circular-timer__gradient-stop-c {
						animation: circular-timer-gradient-c 4s ease-in-out infinite;
					}

					@keyframes circular-timer-gradient-a {
						0%, 100% { stop-color: var(--tg-button); }
						50% { stop-color: var(--tg-success); }
					}

					@keyframes circular-timer-gradient-b {
						0%, 100% { stop-color: var(--tg-success); }
						50% { stop-color: var(--tg-warning); }
					}

					@keyframes circular-timer-gradient-c {
						0%, 100% { stop-color: var(--tg-warning); }
						50% { stop-color: var(--tg-button); }
					}

					@media (prefers-reduced-motion: reduce) {
						.circular-timer__progress,
						.circular-timer__gradient-stop-a,
						.circular-timer__gradient-stop-b,
						.circular-timer__gradient-stop-c {
							animation: none;
							transition: stroke 0.3s ease;
						}
					}
				`}
			</style>
			<defs>
				<linearGradient id={gradientId} x1="16%" y1="18%" x2="86%" y2="82%">
					<stop className="circular-timer__gradient-stop-a" offset="0%" stopColor="var(--tg-button)" />
					<stop className="circular-timer__gradient-stop-b" offset="52%" stopColor="var(--tg-success)" />
					<stop className="circular-timer__gradient-stop-c" offset="100%" stopColor="var(--tg-warning)" />
				</linearGradient>
			</defs>
			<circle
				cx={center}
				cy={center}
				r={radius}
				fill="none"
				stroke="var(--tg-secondary-bg)"
				strokeWidth={8}
			/>
			<circle
				className={`circular-timer__progress${status === 'running' ? ' circular-timer__progress--running' : ''}`}
				cx={center}
				cy={center}
				r={radius}
				fill="none"
				stroke={progressStroke}
				strokeWidth={8}
				strokeLinecap="round"
				strokeDasharray={circumference}
				strokeDashoffset={strokeDashoffset}
				transform={`rotate(-90 ${center} ${center})`}
			/>
			<text
				x={center}
				y={center}
				fontSize={size > 180 ? 48 : 32}
				fontWeight={600}
				fill={status === 'finished' ? 'var(--tg-success)' : 'var(--tg-text)'}
				fontFamily="var(--font-mono)"
				textAnchor="middle"
				dominantBaseline="central"
			>
				{formatTime(remaining)}
			</text>
			<text
				x={center}
				y={center + size * 0.18}
				fontSize={13}
				fill="var(--tg-hint)"
				textAnchor="middle"
				dominantBaseline="central"
			>
				{caption}
			</text>
		</svg>
	)
}
