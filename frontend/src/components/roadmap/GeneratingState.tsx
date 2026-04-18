import { Body, Caption, Skeleton } from '../ui'

export function GeneratingState() {
  return (
    <div
      style={{
        minHeight: '300px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <style>
        {`
          @keyframes roadmap-dots-pulse {
            0% { opacity: 0.3; }
            50% { opacity: 1; }
            100% { opacity: 0.3; }
          }

          .roadmap-dots {
            display: inline-flex;
            gap: 8px;
          }

          .roadmap-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--tg-button);
            animation: roadmap-dots-pulse 1.2s ease-in-out infinite;
          }

          .roadmap-dot--1 { animation-delay: 0s; }
          .roadmap-dot--2 { animation-delay: 0.2s; }
          .roadmap-dot--3 { animation-delay: 0.4s; }

          .roadmap-reduced-motion {
            display: none;
          }

          @media (prefers-reduced-motion: reduce) {
            .roadmap-dots {
              display: none;
            }

            .roadmap-reduced-motion {
              display: block;
              width: 140px;
            }

            .roadmap-dot {
              animation: none;
            }
          }
        `}
      </style>

      <div style={{ textAlign: 'center' }}>
        <div className="roadmap-dots" aria-hidden="true">
          <span className="roadmap-dot roadmap-dot--1" />
          <span className="roadmap-dot roadmap-dot--2" />
          <span className="roadmap-dot roadmap-dot--3" />
        </div>

        <div className="roadmap-reduced-motion">
          <Skeleton height={14} borderRadius="var(--radius-full)" />
        </div>

        <Body style={{ color: 'var(--tg-hint)', marginTop: '20px' }}>Составляю твой план...</Body>
        <Caption style={{ opacity: 0.6, marginTop: '8px', display: 'inline-block' }}>
          Это займёт несколько секунд
        </Caption>
      </div>
    </div>
  )
}