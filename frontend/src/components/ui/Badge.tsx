import { CSSProperties, ReactNode } from 'react'

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

export type BadgeProps = {
	variant: BadgeVariant
	children: ReactNode
}

const variantStyles: Record<BadgeVariant, CSSProperties> = {
	default: {
		background: 'var(--tg-secondary-bg)',
		color: 'var(--tg-text)',
	},
	success: {
		background: 'rgba(56, 161, 105, 0.18)',
		color: 'var(--tg-success)',
	},
	warning: {
		background: 'rgba(214, 158, 46, 0.2)',
		color: 'var(--tg-warning)',
	},
	danger: {
		background: 'rgba(229, 62, 62, 0.18)',
		color: 'var(--tg-destructive)',
	},
	info: {
		background: 'rgba(59, 130, 246, 0.18)',
		color: 'var(--tg-link)',
	},
}

export function Badge({ variant, children }: BadgeProps) {
	return (
		<span
			style={{
				...variantStyles[variant],
				display: 'inline-flex',
				alignItems: 'center',
				justifyContent: 'center',
				fontSize: '11px',
				fontWeight: 600,
				padding: '2px 8px',
				lineHeight: 1.4,
				borderRadius: 'var(--radius-full)',
			}}
		>
			{children}
		</span>
	)
}
