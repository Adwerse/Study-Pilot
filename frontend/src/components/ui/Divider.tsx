import { CSSProperties } from 'react'

export type DividerProps = {
	style?: CSSProperties
}

export function Divider({ style }: DividerProps) {
	return (
		<hr
			style={{
				border: 0,
				borderTop: '0.5px solid var(--tg-hint)',
				opacity: 0.15,
				width: '100%',
				...style,
			}}
		/>
	)
}
