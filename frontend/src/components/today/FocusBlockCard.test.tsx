import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { FocusBlock } from '../../types/api'
import { FocusBlockCard } from './FocusBlockCard'

describe('FocusBlockCard', () => {
	const mockBlock: FocusBlock = {
		title: 'Review lists',
		topic: 'Python basics',
		duration_minutes: 25,
		description: 'Study list comprehension',
		priority: 1,
	}

	it('shows title and description', () => {
		render(
			<FocusBlockCard
				block={mockBlock}
				index={0}
				isDone={false}
				isActive={false}
				onStart={() => undefined}
				onMarkDone={() => undefined}
			/>,
		)

		expect(screen.getByText('Review lists')).toBeInTheDocument()
		expect(screen.getByText('Study list comprehension')).toBeInTheDocument()
	})

	it('shows the Start button when the block is inactive', () => {
		render(
			<FocusBlockCard
				block={mockBlock}
				index={0}
				isDone={false}
				isActive={false}
				onStart={() => undefined}
				onMarkDone={() => undefined}
			/>,
		)

		expect(screen.getByText('Start')).toBeInTheDocument()
	})

	it('shows the Finish button when the block is active', () => {
		render(
			<FocusBlockCard
				block={mockBlock}
				index={0}
				isDone={false}
				isActive={true}
				onStart={() => undefined}
				onMarkDone={() => undefined}
			/>,
		)

		expect(screen.getByText('Finish')).toBeInTheDocument()
	})

	it('calls onStart when Start is clicked', async () => {
		const onStart = vi.fn()
		const user = userEvent.setup()

		render(
			<FocusBlockCard
				block={mockBlock}
				index={0}
				isDone={false}
				isActive={false}
				onStart={onStart}
				onMarkDone={() => undefined}
			/>,
		)

		await user.click(screen.getByText('Start'))
		expect(onStart).toHaveBeenCalledTimes(1)
	})

	it('shows strikethrough text and a check when isDone', () => {
		render(
			<FocusBlockCard
				block={mockBlock}
				index={0}
				isDone={true}
				isActive={false}
				onStart={() => undefined}
				onMarkDone={() => undefined}
			/>,
		)

		expect(screen.getByText('Review lists')).toHaveStyle('text-decoration: line-through')
		expect(screen.getByText('Done')).toBeInTheDocument()
	})
})
