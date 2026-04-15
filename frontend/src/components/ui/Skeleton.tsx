import { CSSProperties } from 'react'

export type SkeletonProps = {
	width?: string | number
	height?: string | number
	borderRadius?: string
	lines?: number
}

function toCssSize(value: string | number | undefined, fallback: string): string {
	if (typeof value === 'number') {
		return `${value}px`
	}

	return value ?? fallback
}

function SkeletonLine({ width, height, borderRadius }: Required<Pick<SkeletonProps, 'width' | 'height' | 'borderRadius'>>) {
	const lineStyle: CSSProperties = {
		width: toCssSize(width, '100%'),
		height: toCssSize(height, '16px'),
		borderRadius,
		background: 'var(--tg-secondary-bg)',
		animation: 'tg-skeleton-shimmer 1.5s ease-in-out infinite',
	}

	return <div style={lineStyle} />
}

export function Skeleton({ width = '100%', height = '16px', borderRadius = 'var(--radius-sm)', lines = 1 }: SkeletonProps) {
	const safeLines = Math.max(1, lines)

	if (safeLines === 1) {
		return (
			<>
				<style>{'@keyframes tg-skeleton-shimmer { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }'}</style>
				<SkeletonLine width={width} height={height} borderRadius={borderRadius} />
			</>
		)
	}

	return (
		<>
			<style>{'@keyframes tg-skeleton-shimmer { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }'}</style>
			<div style={{ display: 'grid', gap: '8px', width: toCssSize(width, '100%') }}>
				{Array.from({ length: safeLines }).map((_, index) => (
					<SkeletonLine key={index} width="100%" height={height} borderRadius={borderRadius} />
				))}
			</div>
		</>
	)
}
