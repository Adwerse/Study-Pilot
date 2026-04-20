import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { PlanStage } from '../../types/api'
import { StageProgress } from './StageProgress'

describe('StageProgress', () => {
	const mockStage: PlanStage = {
		id: '1',
		plan_id: 'p1',
		week_number: 2,
		title: 'Структуры данных',
		deliverable: 'Реализовать стек и очередь',
		status: 'in_progress',
		order_index: 1,
	}

	it('отображает название этапа', () => {
		render(<StageProgress stage={mockStage} completedToday={2} totalToday={4} />)
		expect(screen.getByText('Структуры данных')).toBeInTheDocument()
	})

	it('показывает правильный счётчик блоков', () => {
		render(<StageProgress stage={mockStage} completedToday={2} totalToday={4} />)
		expect(screen.getByText(/2 из 4/)).toBeInTheDocument()
	})

	it('обрезает длинный deliverable', () => {
		const longStage = { ...mockStage, deliverable: 'А'.repeat(100) }
		render(<StageProgress stage={longStage} completedToday={2} totalToday={4} />)

		const element = screen.getByText(/\.\.\./)
		expect(element.textContent?.length).toBeLessThanOrEqual(83)
	})

	it('ширина прогресс-бара соответствует прогрессу', () => {
		const { container } = render(<StageProgress stage={mockStage} completedToday={1} totalToday={4} />)
		const bar = container.querySelector('[data-testid="progress-fill"]')

		expect(bar).toHaveStyle('width: 25%')
	})
})
