import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { DifficultyPicker } from './DifficultyPicker'

describe('DifficultyPicker', () => {
	it('рендерит 5 кнопок сложности', () => {
		render(<DifficultyPicker onSelect={() => undefined} loading={false} />)

		expect(screen.getAllByRole('button')).toHaveLength(5)
	})

	it('вызывает onSelect с правильным значением', async () => {
		const onSelect = vi.fn()
		const user = userEvent.setup()

		render(<DifficultyPicker onSelect={onSelect} loading={false} />)
		const buttons = screen.getAllByRole('button')

		await user.click(buttons[2])

		expect(onSelect).toHaveBeenCalledWith(3)
	})

	it('блокирует кнопки при loading', () => {
		render(<DifficultyPicker onSelect={() => undefined} loading={true} />)

		screen.getAllByRole('button').forEach((button) => {
			expect(button).toHaveStyle('pointer-events: none')
		})
	})
})
