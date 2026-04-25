import { CSSProperties } from 'react'
import type { BadgeVariant } from '../ui/Badge'
import type { FocusBlock } from '../../types/api'
import { Badge, Button, Caption, Card, Subtitle } from '../ui'

type FocusBlockCardProps = {
	block: FocusBlock
	index: number
	isDone: boolean
	isActive: boolean
	pomodoroCount?: number
	onPomodoroCountChange?: (count: number) => void
	onStart: () => void
	onMarkDone: () => void
}

function getPriorityMeta(priority: FocusBlock['priority']): { label: string; variant: BadgeVariant } {
	switch (priority) {
		case 1:
			return { label: 'Main', variant: 'danger' }
		case 2:
			return { label: 'Important', variant: 'warning' }
		case 3:
			return { label: 'Useful', variant: 'default' }
		default:
			return { label: 'Bonus', variant: 'default' }
	}
}

export function FocusBlockCard({
	block,
	index,
	isDone,
	isActive,
	pomodoroCount = 1,
	onPomodoroCountChange,
	onStart,
	onMarkDone,
}: FocusBlockCardProps) {
	const priority = getPriorityMeta(block.priority)
	const safePomodoroCount = Math.min(5, Math.max(1, pomodoroCount))
	const wrapperStyle: CSSProperties = {
		opacity: isDone ? 0.55 : 1,
		pointerEvents: isDone ? 'none' : 'auto',
		borderLeft: isActive ? '3px solid var(--tg-button)' : '3px solid transparent',
		backgroundColor: isActive ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
		background: isActive ? 'color-mix(in srgb, var(--tg-button) 5%, transparent)' : 'transparent',
		borderRadius: 'var(--radius-md)',
		paddingLeft: isActive ? '0' : '0',
		['--focus-block-delay' as string]: `${index * 80}ms`,
	}

	return (
		<div className="today-focus-block-card" style={wrapperStyle}>
			<style>
				{`
					@keyframes today-focus-card-enter {
						from {
							opacity: 0;
							transform: translateY(8px);
						}
						to {
							opacity: 1;
							transform: translateY(0);
						}
					}

					@keyframes today-focus-card-pulse {
						0%,
						100% {
							opacity: 1;
						}
						50% {
							opacity: 0.55;
						}
					}

					@media (prefers-reduced-motion: no-preference) {
						.today-focus-block-card {
							opacity: 0;
							transform: translateY(8px);
							animation: today-focus-card-enter 300ms ease-out forwards;
							animation-delay: var(--focus-block-delay, 0ms);
						}

						.today-focus-block-card [data-pulse='true'] {
							animation: today-focus-card-pulse 1.4s ease-in-out infinite;
						}
					}
				`}
			</style>

			<Card>
				<div>
					<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
						<Badge variant={priority.variant}>{priority.label}</Badge>
						<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
							<Caption style={{ color: 'var(--tg-hint)' }}>{block.duration_minutes} min</Caption>
							<select
								aria-label="Pomodoro count"
								value={safePomodoroCount}
								disabled={isDone || isActive}
								onChange={(event) => onPomodoroCountChange?.(Number(event.target.value))}
								style={{
									height: '30px',
									border: 'none',
									borderRadius: 'var(--radius-full)',
									background: 'var(--tg-bg)',
									color: 'var(--tg-text)',
									fontSize: 'var(--text-xs)',
									fontWeight: 600,
									padding: '0 8px',
									opacity: isDone || isActive ? 0.55 : 1,
									cursor: isDone || isActive ? 'default' : 'pointer',
								}}
							>
								{[1, 2, 3, 4, 5].map((count) => (
									<option key={count} value={count}>
										{count}x
									</option>
								))}
							</select>
						</div>
					</div>

					<Subtitle
						style={{
							marginTop: '8px',
							textDecoration: isDone ? 'line-through' : 'none',
						}}
					>
						{block.title}
					</Subtitle>

					<Caption
						style={{
							display: 'block',
							marginTop: '4px',
							color: 'var(--tg-hint)',
						}}
					>
						{block.description}
					</Caption>

					<div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
						{!isDone && !isActive ? (
							<Button variant="primary" size="sm" onClick={onStart}>
								Start
							</Button>
						) : null}

						{isActive ? (
							<>
								<Button variant="secondary" size="sm" onClick={onMarkDone}>
									Finish
								</Button>
								<Caption
									data-pulse="true"
									style={{
										color: 'var(--tg-button)',
										fontSize: 'var(--text-xs)',
									}}
								>
									Session running...
								</Caption>
							</>
						) : null}

						{isDone ? (
							<>
								<span aria-hidden="true" style={{ display: 'inline-flex', color: 'var(--tg-success)' }}>
									<svg viewBox="0 0 24 24" width="16" height="16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path
											d="M20 6L9 17L4 12"
											stroke="currentColor"
											strokeWidth="2.5"
											strokeLinecap="round"
											strokeLinejoin="round"
										/>
									</svg>
								</span>
								<Caption style={{ color: 'var(--tg-hint)' }}>Done</Caption>
							</>
						) : null}
					</div>
				</div>
			</Card>
		</div>
	)
}
