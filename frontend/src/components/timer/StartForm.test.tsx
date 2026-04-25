import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { StartForm } from './StartForm'

describe('StartForm', () => {
	it('кнопка задизейблена при короткой теме', () => {
		render(<StartForm onStart={() => undefined} loading={false} />)

		expect(screen.getByRole('button')).toBeDisabled()
	})

	it('принимает suggestedTopic как начальное значение', () => {
		render(<StartForm onStart={() => undefined} loading={false} suggestedTopic="Python basics" />)

		expect(screen.getByDisplayValue('Python basics')).toBeInTheDocument()
	})

	it('вызывает onStart с темой', async () => {
		const onStart = vi.fn()
		const user = userEvent.setup()

		render(<StartForm onStart={onStart} loading={false} />)

		await user.type(screen.getByPlaceholderText(/Что будешь/), 'Алгоритмы сортировки')
		await user.click(screen.getByRole('button'))

		expect(onStart).toHaveBeenCalledWith('Алгоритмы сортировки')
	})
})
