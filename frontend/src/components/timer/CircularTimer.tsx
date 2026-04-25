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
	const radius = (size - 20) / 2
	const circumference = 2 * Math.PI * radius
	const safeProgress = Math.min(1, Math.max(0, progress))
	const strokeDashoffset = circumference * (1 - safeProgress)
	const center = size / 2
	const caption = getCaption(status)

	return (
		<svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={formatTime(remaining)}>
			<style>
				{`
					.circular-timer__progress {
						transition: stroke-dashoffset 1s linear, stroke 0.3s ease;
					}

					@media (prefers-reduced-motion: reduce) {
						.circular-timer__progress {
							transition: stroke 0.3s ease;
						}
					}
				`}
			</style>
			<circle
				cx={center}
				cy={center}
				r={radius}
				fill="none"
				stroke="var(--tg-secondary-bg)"
				strokeWidth={8}
			/>
			<circle
				className="circular-timer__progress"
				cx={center}
				cy={center}
				r={radius}
				fill="none"
				stroke={status === 'finished' ? 'var(--tg-success)' : status === 'paused' ? 'var(--tg-hint)' : 'var(--tg-button)'}
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
