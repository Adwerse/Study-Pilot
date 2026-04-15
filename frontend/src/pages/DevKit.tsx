import { useState } from 'react'
import { Badge, Body, Button, Caption, Card, Divider, Hint, Subtitle, Title } from '../components/ui'

const sectionStyle = {
	display: 'grid',
	gap: 'var(--space-3)',
}

const rowStyle = {
	display: 'flex',
	flexWrap: 'wrap' as const,
	gap: 'var(--space-2)',
}

export function DevKit() {
	const [cardClicks, setCardClicks] = useState(0)

	return (
		<main
			style={{
				minHeight: '100%',
				padding: 'var(--space-4)',
				display: 'grid',
				gap: 'var(--space-5)',
				background: 'var(--tg-bg)',
			}}
		>
			<header style={{ display: 'grid', gap: 'var(--space-2)' }}>
				<Title>Learning OS UI DevKit</Title>
				<Caption>Component showcase for Telegram Mini App</Caption>
			</header>

			<section style={sectionStyle}>
				<Subtitle>Buttons</Subtitle>
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
						<Body style={{ fontWeight: 600 }}>Variants</Body>
						<div style={rowStyle}>
							<Button variant="primary" size="md">Primary</Button>
							<Button variant="secondary" size="md">Secondary</Button>
							<Button variant="destructive" size="md">Destructive</Button>
							<Button variant="ghost" size="md">Ghost</Button>
						</div>

						<Body style={{ fontWeight: 600 }}>Sizes</Body>
						<div style={rowStyle}>
							<Button variant="primary" size="sm">Small</Button>
							<Button variant="primary" size="md">Medium</Button>
							<Button variant="primary" size="lg">Large</Button>
						</div>

						<Body style={{ fontWeight: 600 }}>States</Body>
						<div style={rowStyle}>
							<Button variant="secondary" size="md" loading>
								Loading
							</Button>
							<Button variant="destructive" size="md" disabled>
								Disabled
							</Button>
						</div>

						<Button variant="primary" size="md" fullWidth>
							Full Width Button
						</Button>
					</div>
				</Card>
			</section>

			<section style={sectionStyle}>
				<Subtitle>Cards</Subtitle>
				<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
					<Card>
						<Body>A regular card without interactivity.</Body>
					</Card>
					<Card onClick={() => setCardClicks((prev) => prev + 1)}>
						<Body>Clickable card. Clicks: {cardClicks}</Body>
						<Hint>Hover and pointer are enabled when onClick is provided.</Hint>
					</Card>
				</div>
			</section>

			<section style={sectionStyle}>
				<Subtitle>Badges</Subtitle>
				<div style={rowStyle}>
					<Badge variant="default">Default</Badge>
					<Badge variant="success">Success</Badge>
					<Badge variant="warning">Warning</Badge>
					<Badge variant="danger">Danger</Badge>
					<Badge variant="info">Info</Badge>
				</div>
			</section>

			<section style={sectionStyle}>
				<Subtitle>Typography</Subtitle>
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
						<Title>Title Example</Title>
						<Subtitle>Subtitle Example</Subtitle>
						<Body>Body text example for main content in cards and lists.</Body>
						<Caption>Caption example text</Caption>
						<Hint>Hint example text</Hint>
					</div>
				</Card>
			</section>

			<section style={sectionStyle}>
				<Subtitle>Divider</Subtitle>
				<Card>
					<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
						<Body>Content before divider</Body>
						<Divider />
						<Body>Content after divider</Body>
					</div>
				</Card>
			</section>
		</main>
	)
}
