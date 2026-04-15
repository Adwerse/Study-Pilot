import { Button, Divider, Skeleton, Title } from '../components/ui'

export function KnowledgePage() {
	const handleUpload = () => {
		// TODO: integrate RAG Agent (Sprint 5)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<Title>Knowledge base</Title>

			<Button variant="secondary" size="lg" fullWidth onClick={handleUpload}>
				Upload document
			</Button>

			<Divider />

			<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
				<Skeleton height={14} width="90%" />
				<Skeleton height={14} width="85%" />
				<Skeleton height={14} width="72%" />
			</div>

			<input
				placeholder="Ask a question..."
				style={{
					width: '100%',
					height: '44px',
					padding: '0 var(--space-3)',
					borderRadius: 'var(--radius-md)',
					border: '1px solid rgba(0, 0, 0, 0.08)',
					background: 'var(--tg-secondary-bg)',
					color: 'var(--tg-text)',
					fontSize: 'var(--text-base)',
					outline: 'none',
				}}
			/>
		</div>
	)
}
