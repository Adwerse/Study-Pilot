import { Body } from '../ui'

type DailyNoteProps = {
	note: string
}

export function DailyNote({ note }: DailyNoteProps) {
	return (
		<div
			style={{
				borderLeft: '3px solid var(--tg-button)',
				borderRadius: '0',
				padding: '10px 14px',
				background: 'var(--tg-secondary-bg)',
			}}
		>
			<Body
				style={{
					fontStyle: 'italic',
					color: 'var(--tg-hint)',
				}}
			>
				{note}
			</Body>
		</div>
	)
}
