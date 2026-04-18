import { CSSProperties, FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../ui'
import type { GenerateParams } from '../../hooks/useRoadmap'

type GoalFormProps = {
  onSubmit: (params: GenerateParams) => void
  loading: boolean
}

const fieldStyle: CSSProperties = {
  background: 'var(--tg-secondary-bg)',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  padding: '12px',
  fontSize: 'var(--text-base)',
  color: 'var(--tg-text)',
  width: '100%',
}

const labelStyle: CSSProperties = {
  display: 'block',
  fontSize: 'var(--text-sm)',
  color: 'var(--tg-hint)',
  marginBottom: '6px',
}

export function GoalForm({ onSubmit, loading }: GoalFormProps) {
  const [goal, setGoal] = useState('')
  const [level, setLevel] = useState<GenerateParams['level']>('beginner')
  const [weeklyHours, setWeeklyHours] = useState(10)
  const [deadline, setDeadline] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const tomorrowDate = useMemo(() => {
    const now = new Date()
    now.setDate(now.getDate() + 1)
    return now.toISOString().slice(0, 10)
  }, [])

  useEffect(() => {
    if (!textareaRef.current) {
      return
    }

    textareaRef.current.style.height = '80px'
    const targetHeight = Math.min(200, Math.max(80, textareaRef.current.scrollHeight))
    textareaRef.current.style.height = `${targetHeight}px`
  }, [goal])

  const isDisabled = goal.length < 10 || loading

  const submit = () => {
    if (isDisabled) {
      return
    }

    onSubmit({
      goal,
      level,
      weekly_hours: weeklyHours,
      deadline: deadline || undefined,
    })
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit()
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '20px' }}>
      <div>
        <label htmlFor="goal" style={labelStyle}>
          Какую цель хочешь достичь?
        </label>

        <div style={{ position: 'relative' }}>
          <textarea
            id="goal"
            ref={textareaRef}
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="Например: выучить Python для анализа данных"
            minLength={10}
            maxLength={300}
            rows={3}
            style={{
              ...fieldStyle,
              minHeight: '80px',
              maxHeight: '200px',
              resize: 'none',
              overflowY: 'auto',
              paddingBottom: '24px',
              lineHeight: 1.4,
            }}
          />
          <span
            style={{
              position: 'absolute',
              right: '12px',
              bottom: '8px',
              fontSize: '13px',
              color: 'var(--tg-hint)',
              pointerEvents: 'none',
            }}
          >
            {goal.length}/300
          </span>
        </div>
      </div>

      <div>
        <label htmlFor="level" style={labelStyle}>
          Уровень подготовки
        </label>
        <select
          id="level"
          value={level}
          onChange={(event) => setLevel(event.target.value as GenerateParams['level'])}
          style={fieldStyle}
        >
          <option value="beginner">С нуля</option>
          <option value="intermediate">Базовые знания есть</option>
          <option value="advanced">Продвинутый</option>
        </select>
      </div>

      <div>
        <label htmlFor="weekly-hours" style={labelStyle}>
          Часов в неделю
        </label>
        <div
          style={{
            fontSize: 'var(--text-lg)',
            fontWeight: 500,
            color: 'var(--tg-text)',
            marginBottom: '8px',
          }}
        >
          {weeklyHours} ч/нед
        </div>
        <input
          id="weekly-hours"
          type="range"
          min={2}
          max={40}
          step={1}
          value={weeklyHours}
          onChange={(event) => setWeeklyHours(Number(event.target.value))}
          style={{ width: '100%' }}
        />
      </div>

      <div>
        <label htmlFor="deadline" style={labelStyle}>
          Дедлайн (необязательно)
        </label>
        <input
          id="deadline"
          type="date"
          min={tomorrowDate}
          value={deadline}
          onChange={(event) => setDeadline(event.target.value)}
          style={fieldStyle}
        />
      </div>

      <Button
        variant="primary"
        size="lg"
        fullWidth
        loading={loading}
        disabled={isDisabled}
        onClick={submit}
      >
        Сгенерировать roadmap
      </Button>
    </form>
  )
}