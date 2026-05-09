import { Caption, Card, Subtitle } from '../ui'
import type { TopicFocusMetric } from '../../types/api'
import { formatMinutes } from '../../utils/analyticsFormatters'

export interface TopicProgressListProps {
	topics: TopicFocusMetric[]
}

function getTopicName(metric: TopicFocusMetric): string {
	return typeof metric.topic === 'string' && metric.topic.trim() ? metric.topic.trim() : 'Без темы'
}

function getTopicMinutes(metric: TopicFocusMetric): number {
	return Number.isFinite(metric.minutes) ? Math.max(0, Math.round(metric.minutes)) : 0
}

export function TopicProgressList({ topics }: TopicProgressListProps) {
	const normalizedTopics = topics
		.map((topic) => ({
			name: getTopicName(topic),
			minutes: getTopicMinutes(topic),
		}))
		.filter((topic) => topic.minutes > 0 || topic.name)
	const maxMinutes = Math.max(0, ...normalizedTopics.map((topic) => topic.minutes))

	return (
		<Card>
			<section className="analytics-section" aria-label="Прогресс по темам">
				<Subtitle>Темы</Subtitle>

				{normalizedTopics.length === 0 ? (
					<Caption>Пока нет данных по темам</Caption>
				) : (
					<div className="analytics-topic-list">
						{normalizedTopics.map((topic) => {
							const width = maxMinutes > 0 ? Math.max(4, Math.round((topic.minutes / maxMinutes) * 100)) : 0

							return (
								<div className="analytics-topic-row" key={`${topic.name}-${topic.minutes}`}>
									<div className="analytics-topic-meta">
										<span className="analytics-topic-name" title={topic.name}>
											{topic.name}
										</span>
										<Caption style={{ whiteSpace: 'nowrap' }}>{formatMinutes(topic.minutes)}</Caption>
									</div>
									<div className="analytics-progress-track" aria-hidden="true">
										<div className="analytics-progress-fill" style={{ width: `${width}%` }} />
									</div>
								</div>
							)
						})}
					</div>
				)}
			</section>
		</Card>
	)
}
