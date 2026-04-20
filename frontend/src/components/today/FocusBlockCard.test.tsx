import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { FocusBlock } from '../../types/api'
import { FocusBlockCard } from './FocusBlockCard'

describe('FocusBlockCard', () => {
	const mockBlock: FocusBlock = {
		title: 'Разобрать списки',
		topic: 'Python basics',
		duration_minutes: 25,
		description: 'Изучить list comprehension',
		priority: 1,
	}

	it('показывает заголовок и описание', () => {
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

		expect(screen.getByText('Разобрать списки')).toBeInTheDocument()
		expect(screen.getByText('Изучить list comprehension')).toBeInTheDocument()
	})

	it('показывает кнопку Начать если блок не активен', () => {
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

		expect(screen.getByText('Начать')).toBeInTheDocument()
	})

	it('показывает кнопку Завершить если блок активен', () => {
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

		expect(screen.getByText('Завершить')).toBeInTheDocument()
	})

	it('вызывает onStart при клике Начать', async () => {
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

		await user.click(screen.getByText('Начать'))
		expect(onStart).toHaveBeenCalledTimes(1)
	})

	it('показывает зачёркнутый текст и галочку если isDone', () => {
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

		expect(screen.getByText('Разобрать списки')).toHaveStyle('text-decoration: line-through')
		expect(screen.getByText('Выполнено')).toBeInTheDocument()
	})
})
