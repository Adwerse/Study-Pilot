import { useEffect, useRef, useState } from 'react'
import { Button, Caption } from '../ui'

type StartFormProps = {
	onStart: (topic: string) => void
	loading: boolean
	suggestedTopic?: string
}

export function StartForm({ onStart, loading, suggestedTopic }: StartFormProps) {
	const [topic, setTopic] = useState(suggestedTopic ?? '')
	const inputRef = useRef<HTMLInputElement>(null)
	const isDisabled = topic.trim().length < 3 || loading

	useEffect(() => {
		inputRef.current?.focus()
	}, [])

	return (
		<div style={{ display: 'grid', gap: '12px', width: '100%' }}>
			<label style={{ display: 'grid', gap: '8px' }}>
				<span style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--tg-text)' }}>Session topic</span>
				<input
					ref={inputRef}
					value={topic}
					placeholder="What will you study?"
					onChange={(event) => setTopic(event.target.value)}
					style={{
						width: '100%',
						minHeight: '48px',
						border: '1px solid var(--tg-secondary-bg)',
						borderRadius: 'var(--radius-md)',
						background: 'var(--tg-secondary-bg)',
						color: 'var(--tg-text)',
						fontSize: 'var(--text-base)',
						padding: '0 14px',
						outline: 'none',
						boxSizing: 'border-box',
					}}
				/>
			</label>

			<Caption style={{ display: 'block' }}>25 minutes of deep work</Caption>

			<Button
				variant="primary"
				size="md"
				fullWidth
				disabled={isDisabled}
				loading={loading}
				onClick={() => {
					if (!isDisabled) {
						onStart(topic.trim())
					}
				}}
			>
				Start session
			</Button>
		</div>
	)
}
