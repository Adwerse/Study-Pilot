import { CSSProperties, ReactNode, useState } from 'react'

export type CardPadding = 'sm' | 'md' | 'lg'

export type CardProps = {
	padding?: CardPadding
	onClick?: () => void
	children: ReactNode
}

const paddingBySize: Record<CardPadding, string> = {
	sm: '12px',
	md: '16px',
	lg: '20px',
}

export function Card({ padding = 'md', onClick, children }: CardProps) {
	const [hovered, setHovered] = useState(false)
	const isClickable = Boolean(onClick)

	const cardStyle: CSSProperties = {
		background: 'var(--tg-secondary-bg)',
		borderRadius: 'var(--radius-md)',
		padding: paddingBySize[padding],
		boxShadow: hovered && isClickable ? 'var(--shadow-md)' : 'var(--shadow-sm)',
		cursor: isClickable ? 'pointer' : 'default',
		transition: 'transform 0.2s ease, box-shadow 0.2s ease',
		transform: hovered && isClickable ? 'translateY(-1px)' : 'translateY(0)',
	}

	return (
		<div
			style={cardStyle}
			onClick={onClick}
			onMouseEnter={() => setHovered(true)}
			onMouseLeave={() => setHovered(false)}
		>
			{children}
		</div>
	)
}
