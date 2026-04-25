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
		title: 'Data structures',
		deliverable: 'Implement a stack and a queue',
		status: 'in_progress',
		order_index: 1,
	}

	it('renders the stage title', () => {
		render(<StageProgress stage={mockStage} completedToday={2} totalToday={4} />)
		expect(screen.getByText('Data structures')).toBeInTheDocument()
	})

	it('shows the correct block counter', () => {
		render(<StageProgress stage={mockStage} completedToday={2} totalToday={4} />)
		expect(screen.getByText(/2 of 4/)).toBeInTheDocument()
	})

	it('truncates a long deliverable', () => {
		const longStage = { ...mockStage, deliverable: 'A'.repeat(100) }
		render(<StageProgress stage={longStage} completedToday={2} totalToday={4} />)

		const element = screen.getByText(/\.\.\./)
		expect(element.textContent?.length).toBeLessThanOrEqual(83)
	})

	it('sets the progress bar width from progress', () => {
		const { container } = render(<StageProgress stage={mockStage} completedToday={1} totalToday={4} />)
		const bar = container.querySelector('[data-testid="progress-fill"]')

		expect(bar).toHaveStyle('width: 25%')
	})
})
