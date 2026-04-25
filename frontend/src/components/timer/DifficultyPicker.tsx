import { CSSProperties } from 'react'
import { Caption, Title } from '../ui'

type DifficultyPickerProps = {
	onSelect: (difficulty: number) => void
	loading: boolean
}

const difficulties = [
	{ value: 1, emoji: '😴', label: 'Easy' },
	{ value: 2, emoji: '🙂', label: '' },
	{ value: 3, emoji: '😤', label: '' },
	{ value: 4, emoji: '🔥', label: '' },
	{ value: 5, emoji: '🤯', label: 'Hard' },
]

const backdropStyle: CSSProperties = {
	position: 'fixed',
	inset: 0,
	background: 'rgba(0,0,0,0.5)',
	zIndex: 200,
	animation: 'difficulty-picker-fade-in 200ms ease-out',
}

const sheetStyle: CSSProperties = {
	position: 'fixed',
	bottom: 0,
	left: 0,
	right: 0,
	background: 'var(--tg-bg)',
	borderRadius: '20px 20px 0 0',
	padding: '24px 20px 40px',
	zIndex: 201,
	animation: 'difficulty-picker-slide-up 250ms ease-out',
	boxShadow: '0 -12px 32px rgba(0,0,0,0.16)',
}

export function DifficultyPicker({ onSelect, loading }: DifficultyPickerProps) {
	return (
		<>
			<style>
				{`
					@keyframes difficulty-picker-fade-in {
						from { opacity: 0; }
						to { opacity: 1; }
					}

					@keyframes difficulty-picker-slide-up {
						from { transform: translateY(100%); }
						to { transform: translateY(0); }
					}

					.difficulty-picker__button {
						transition: transform 100ms ease;
					}

					.difficulty-picker__button:hover,
					.difficulty-picker__button:active {
						transform: scale(1.1);
					}
				`}
			</style>
			<div style={backdropStyle} aria-hidden="true" />
			<div role="dialog" aria-modal="true" aria-labelledby="difficulty-picker-title" style={sheetStyle}>
				<div id="difficulty-picker-title" style={{ display: 'grid', gap: '8px', textAlign: 'center' }}>
					<Title style={{ fontSize: 'var(--text-xl)' }}>How did the session go?</Title>
					<Caption>Rate the material difficulty</Caption>
				</div>

				<div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '24px' }}>
					{difficulties.map((difficulty) => (
						<button
							key={difficulty.value}
							type="button"
							aria-label={`Difficulty ${difficulty.value}`}
							className="difficulty-picker__button"
							disabled={loading}
							onClick={() => onSelect(difficulty.value)}
							style={{
								width: '52px',
								height: '52px',
								borderRadius: '50%',
								border: 'none',
								background: 'var(--tg-secondary-bg)',
								color: 'var(--tg-text)',
								display: 'grid',
								placeItems: 'center',
								cursor: 'pointer',
								opacity: loading ? 0.5 : 1,
								pointerEvents: loading ? 'none' : 'auto',
							}}
						>
							<span aria-hidden="true" style={{ fontSize: '24px', lineHeight: 1 }}>
								{difficulty.emoji}
							</span>
							<span
								style={{
									fontSize: '10px',
									color: 'var(--tg-hint)',
									lineHeight: 1,
									minHeight: '10px',
								}}
							>
								{difficulty.label}
							</span>
						</button>
					))}
				</div>
			</div>
		</>
	)
}
