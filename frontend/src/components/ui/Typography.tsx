import { CSSProperties, ReactNode } from 'react'

type TextProps = {
	children: ReactNode
	style?: CSSProperties
	className?: string
}

export function Title({ children, style, className }: TextProps) {
	return (
		<div
			className={className}
			style={{
				fontSize: 'var(--text-2xl)',
				fontWeight: 600,
				color: 'var(--tg-text)',
				...style,
			}}
		>
			{children}
		</div>
	)
}

export function Subtitle({ children, style, className }: TextProps) {
	return (
		<div
			className={className}
			style={{
				fontSize: 'var(--text-lg)',
				fontWeight: 500,
				color: 'var(--tg-text)',
				...style,
			}}
		>
			{children}
		</div>
	)
}

export function Body({ children, style, className }: TextProps) {
	return (
		<p
			className={className}
			style={{
				fontSize: 'var(--text-base)',
				color: 'var(--tg-text)',
				...style,
			}}
		>
			{children}
		</p>
	)
}

export function Caption({ children, style, className }: TextProps) {
	return (
		<span
			className={className}
			style={{
				fontSize: 'var(--text-sm)',
				color: 'var(--tg-hint)',
				...style,
			}}
		>
			{children}
		</span>
	)
}

export function Hint({ children, style, className }: TextProps) {
	return (
		<span
			className={className}
			style={{
				fontSize: 'var(--text-xs)',
				color: 'var(--tg-hint)',
				...style,
			}}
		>
			{children}
		</span>
	)
}
