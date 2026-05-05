import { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { BottomTab } from './BottomTab'

type TabConfig = {
	to: '/today' | '/roadmap' | '/knowledge' | '/analytics'
	label: string
	icon: ReactNode
}

function IconWrapper({ children }: { children: ReactNode }) {
	return (
		<span style={{ width: '22px', height: '22px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
			{children}
		</span>
	)
}

const tabs: TabConfig[] = [
	{
		to: '/today',
		label: 'Today',
		icon: (
			<IconWrapper>
				<svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" fill="none" strokeWidth="1.5">
					<path d="M3.75 10.5 12 3.75l8.25 6.75v9a.75.75 0 0 1-.75.75h-5.25v-6h-4.5v6H4.5a.75.75 0 0 1-.75-.75v-9Z" />
				</svg>
			</IconWrapper>
		),
	},
	{
		to: '/roadmap',
		label: 'Roadmap',
		icon: (
			<IconWrapper>
				<svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" fill="none" strokeWidth="1.5">
					<path d="M4.5 5.25h8.25a2.25 2.25 0 0 1 0 4.5H9.75a2.25 2.25 0 1 0 0 4.5h4.5a2.25 2.25 0 1 1 0 4.5H4.5" />
					<path d="M4.5 5.25v13.5" />
				</svg>
			</IconWrapper>
		),
	},
	{
		to: '/knowledge',
		label: 'База знаний',
		icon: (
			<IconWrapper>
				<svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" fill="none" strokeWidth="1.5">
					<path d="M4.5 6.75A2.25 2.25 0 0 1 6.75 4.5h12.75v14.25H6.75A2.25 2.25 0 0 0 4.5 21V6.75Z" />
					<path d="M6.75 18.75V21" />
					<path d="M9 8.25h7.5" />
					<path d="M9 11.25h6" />
				</svg>
			</IconWrapper>
		),
	},
	{
		to: '/analytics',
		label: 'Analytics',
		icon: (
			<IconWrapper>
				<svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" fill="none" strokeWidth="1.5">
					<path d="M4.5 19.5h15" />
					<path d="M7.5 16.5v-4.5" />
					<path d="M12 16.5V9" />
					<path d="M16.5 16.5V6" />
				</svg>
			</IconWrapper>
		),
	},
]

export function BottomNav() {
	const location = useLocation()

	return (
		<nav
			style={{
				position: 'fixed',
				bottom: 0,
				left: 0,
				right: 0,
				background: 'var(--tg-bg)',
				borderTop: '0.5px solid rgba(0, 0, 0, 0.08)',
				display: 'grid',
				gridTemplateColumns: 'repeat(4, 1fr)',
				paddingBottom: 'env(safe-area-inset-bottom, 0px)',
				zIndex: 100,
			}}
		>
			{tabs.map((tab) => (
				<BottomTab key={tab.to} to={tab.to} label={tab.label} icon={tab.icon} active={location.pathname === tab.to} />
			))}
		</nav>
	)
}
