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
    title: 'Python fundamentals',
    deliverable: 'Write the first script',
    status: 'in_progress',
    order_index: 0,
  }

  it('renders the week number', () => {
    render(<StageCard stage={mockStage} index={0} />)
    expect(screen.getByText(/Week 1/)).toBeInTheDocument()
  })

  it('renders the title and deliverable', () => {
    render(<StageCard stage={mockStage} index={0} />)
    expect(screen.getByText('Python fundamentals')).toBeInTheDocument()
    expect(screen.getByText('Write the first script')).toBeInTheDocument()
  })

  it('shows no more than 3 tags and a remainder counter', () => {
    const stage = { ...mockStage, topics: ['a', 'b', 'c', 'd', 'e'] }
    render(<StageCard stage={stage} index={0} />)
    expect(screen.getByText('+2 more')).toBeInTheDocument()
  })

  it('applies the current week style', () => {
    const { container } = render(<StageCard stage={mockStage} index={0} isCurrentWeek />)
    const wrapper = container.firstElementChild as HTMLElement
    expect(wrapper.style.borderLeftWidth).toBe('3px')
    expect(wrapper.style.borderLeftStyle).toBe('solid')
  })
})
