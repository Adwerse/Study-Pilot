import { ReactNode, useState } from 'react'
import { Link } from 'react-router-dom'

export type BottomTabProps = {
	icon: ReactNode
	label: string
	to: string
	active: boolean
}

export function BottomTab({ icon, label, to, active }: BottomTabProps) {
	const [pressed, setPressed] = useState(false)

	return (
		<Link
			to={to}
			onMouseDown={() => setPressed(true)}
			onMouseUp={() => setPressed(false)}
			onMouseLeave={() => setPressed(false)}
			onTouchStart={() => setPressed(true)}
			onTouchEnd={() => setPressed(false)}
			style={{
				height: '56px',
				display: 'flex',
				flexDirection: 'column',
				alignItems: 'center',
				justifyContent: 'center',
				gap: '4px',
				textDecoration: 'none',
				color: active ? 'var(--tg-button)' : 'var(--tg-hint)',
				fontSize: 'var(--text-xs)',
				fontWeight: 500,
				transform: pressed ? 'scale(0.92)' : 'scale(1)',
				transition: 'transform 100ms ease, color 100ms ease',
			}}
		>
			{icon}
			<span style={{ maxWidth: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</span>
		</Link>
	)
}
