import { CSSProperties } from 'react'
import type { PlanStage } from '../../types/api'
import { Badge, Body, Card, Divider, Subtitle } from '../ui'

type StageCardProps = {
  stage: PlanStage & { topics?: string[] }
  index: number
  isCurrentWeek?: boolean
}

function getStatusBadge(status: PlanStage['status']) {
  if (status === 'done') {
    return <Badge variant="success">Выполнено</Badge>
  }

  if (status === 'in_progress') {
    return <Badge variant="default">В процессе</Badge>
  }

  return null
}

export function StageCard({ stage, index, isCurrentWeek = false }: StageCardProps) {
  const topics = Array.isArray(stage.topics) ? stage.topics : []
  const visibleTopics = topics.slice(0, 3)
  const hiddenTopicsCount = Math.max(0, topics.length - visibleTopics.length)

  const wrapperStyle: CSSProperties = {
    borderLeftWidth: '3px',
    borderLeftStyle: 'solid',
    borderLeftColor: isCurrentWeek ? 'var(--tg-button, #3b82f6)' : 'transparent',
    borderRadius: 'var(--radius-md)',
    background: isCurrentWeek ? 'color-mix(in srgb, var(--tg-button, #3b82f6) 5%, transparent)' : 'transparent',
    ['--stage-delay' as string]: `${index * 60}ms`,
  }

  return (
    <div className="roadmap-stage-card" style={wrapperStyle}>
      <style>
        {`
          @keyframes roadmap-stage-fade-up {
            from {
              opacity: 0;
              transform: translateY(8px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          @media (prefers-reduced-motion: no-preference) {
            .roadmap-stage-card {
              opacity: 0;
              transform: translateY(8px);
              animation: roadmap-stage-fade-up 300ms ease-out forwards;
              animation-delay: var(--stage-delay, 0ms);
            }
          }
        `}
      </style>

      <Card>
        <div style={{ display: 'grid', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
            <Badge variant="info">Неделя {stage.week_number}</Badge>
            {getStatusBadge(stage.status)}
          </div>

          <Subtitle style={{ marginTop: '8px' }}>{stage.title}</Subtitle>

          <Body
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
              color: 'var(--tg-hint)',
              fontSize: 'var(--text-sm)',
            }}
          >
            <span aria-hidden="true" style={{ display: 'inline-flex', marginTop: '2px' }}>
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M20 6L9 17L4 12"
                  stroke="var(--tg-success)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <span>{stage.deliverable}</span>
          </Body>

          {topics.length > 0 ? (
            <>
              <Divider />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {visibleTopics.map((topic) => (
                  <Badge key={topic} variant="default">
                    {topic}
                  </Badge>
                ))}

                {hiddenTopicsCount > 0 ? <Badge variant="default">+{hiddenTopicsCount} ещё</Badge> : null}
              </div>
            </>
          ) : null}
        </div>
      </Card>
    </div>
  )
}