import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { PlanStage } from '../../types/api'
import { StageCard } from './StageCard'

describe('StageCard', () => {
  const mockStage: PlanStage = {
    id: '1',
    plan_id: 'p1',
    week_number: 1,
    title: 'Основы Python',
    deliverable: 'Написать первый скрипт',
    status: 'in_progress',
    order_index: 0,
  }

  it('отображает номер недели', () => {
    render(<StageCard stage={mockStage} index={0} />)
    expect(screen.getByText(/Неделя 1/)).toBeInTheDocument()
  })

  it('отображает заголовок и deliverable', () => {
    render(<StageCard stage={mockStage} index={0} />)
    expect(screen.getByText('Основы Python')).toBeInTheDocument()
    expect(screen.getByText('Написать первый скрипт')).toBeInTheDocument()
  })

  it('показывает не более 3 тегов + счётчик остатка', () => {
    const stage = { ...mockStage, topics: ['a', 'b', 'c', 'd', 'e'] }
    render(<StageCard stage={stage} index={0} />)
    expect(screen.getByText('+2 ещё')).toBeInTheDocument()
  })

  it('применяет стиль текущей недели', () => {
    const { container } = render(<StageCard stage={mockStage} index={0} isCurrentWeek />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper.style.borderLeftWidth).toBe('3px')
    expect(wrapper.style.borderLeftStyle).toBe('solid')
  })
})