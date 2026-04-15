import { CSSProperties, ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'destructive' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

export type ButtonProps = {
	variant: ButtonVariant
	size: ButtonSize
	fullWidth?: boolean
	loading?: boolean
	disabled?: boolean
	onClick?: () => void
	children: ReactNode
}

const variantStyles: Record<ButtonVariant, CSSProperties> = {
	primary: {
		background: 'var(--tg-button)',
		color: 'var(--tg-button-text)',
	},
	secondary: {
		background: 'var(--tg-secondary-bg)',
		color: 'var(--tg-text)',
	},
	destructive: {
		background: 'var(--tg-destructive)',
		color: '#fff',
	},
	ghost: {
		background: 'transparent',
		color: 'var(--tg-link)',
	},
}

const sizeStyles: Record<ButtonSize, CSSProperties> = {
	sm: {
		minHeight: '32px',
		padding: '0 12px',
		fontSize: 'var(--text-sm)',
	},
	md: {
		minHeight: '40px',
		padding: '0 16px',
		fontSize: 'var(--text-base)',
	},
	lg: {
		minHeight: '48px',
		padding: '0 20px',
		fontSize: 'var(--text-lg)',
	},
}

const baseButtonStyle: CSSProperties = {
	border: 'none',
	borderRadius: 'var(--radius-md)',
	fontWeight: 600,
	display: 'inline-flex',
	alignItems: 'center',
	justifyContent: 'center',
	gap: 'var(--space-2)',
	cursor: 'pointer',
	transition: 'opacity 0.2s ease',
	boxShadow: 'var(--shadow-sm)',
}

const spinnerStyle: CSSProperties = {
	width: '14px',
	height: '14px',
	border: '2px solid transparent',
	borderTopColor: 'currentColor',
	borderRightColor: 'currentColor',
	borderRadius: 'var(--radius-full)',
	animation: 'tg-ui-spin 0.7s linear infinite',
}

export function Button({
	variant,
	size,
	fullWidth = false,
	loading = false,
	disabled = false,
	onClick,
	children,
}: ButtonProps) {
	const isDisabled = disabled || loading

	const buttonStyle: CSSProperties = {
		...baseButtonStyle,
		...variantStyles[variant],
		...sizeStyles[size],
		opacity: isDisabled ? 0.5 : 1,
		pointerEvents: isDisabled ? 'none' : 'auto',
		width: fullWidth ? '100%' : 'auto',
		boxShadow: variant === 'ghost' ? 'none' : baseButtonStyle.boxShadow,
	}

	return (
		<>
			<style>{'@keyframes tg-ui-spin { to { transform: rotate(360deg); } }'}</style>
			<button type="button" onClick={onClick} disabled={isDisabled} style={buttonStyle}>
				{loading ? <span aria-hidden="true" style={spinnerStyle} /> : null}
				<span>{children}</span>
			</button>
		</>
	)
}
