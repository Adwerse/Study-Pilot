import { Component, ErrorInfo, ReactNode } from 'react'
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom'
import { Body, Button, Caption, Card, Title } from './ui'

type ErrorBoundaryProps = {
	children: ReactNode
}

type ErrorBoundaryState = {
	hasError: boolean
}

function ErrorFallback({ onReset }: { onReset?: () => void }) {
	return (
		<div style={{ minHeight: '100%', display: 'grid', placeItems: 'center', padding: 'var(--space-4)' }}>
			<Card>
				<div style={{ display: 'grid', gap: 'var(--space-3)', textAlign: 'center' }}>
					<Title>Something went wrong</Title>
					<Body>StudyPilot could not render this screen.</Body>
					<Caption>Try refreshing the app. If it keeps happening, come back in a minute.</Caption>
					<Button variant="primary" size="md" onClick={onReset ?? (() => window.location.reload())}>
						Reload
					</Button>
				</div>
			</Card>
		</div>
	)
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
	state: ErrorBoundaryState = { hasError: false }

	static getDerivedStateFromError(): ErrorBoundaryState {
		return { hasError: true }
	}

	componentDidCatch(error: Error, errorInfo: ErrorInfo) {
		if (import.meta.env.DEV) {
			console.error('[ui-error]', error, errorInfo)
		}
	}

	render() {
		if (this.state.hasError) {
			return <ErrorFallback onReset={() => this.setState({ hasError: false })} />
		}

		return this.props.children
	}
}

export function RouteErrorFallback() {
	const error = useRouteError()
	const navigate = useNavigate()
	const message = isRouteErrorResponse(error)
		? error.status === 404
			? 'This screen is not available.'
			: 'StudyPilot could not load this screen.'
		: 'StudyPilot could not load this screen.'

	return (
		<div style={{ minHeight: '100%', display: 'grid', placeItems: 'center', padding: 'var(--space-4)' }}>
			<Card>
				<div style={{ display: 'grid', gap: 'var(--space-3)', textAlign: 'center' }}>
					<Title>Screen unavailable</Title>
					<Body>{message}</Body>
					<div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
						<Button variant="secondary" size="md" onClick={() => navigate(-1)}>
							Back
						</Button>
						<Button variant="primary" size="md" onClick={() => window.location.reload()}>
							Reload
						</Button>
					</div>
				</div>
			</Card>
		</div>
	)
}
