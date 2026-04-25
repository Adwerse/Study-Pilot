import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { StartForm } from './StartForm'

describe('StartForm', () => {
	it('disables the button for a short topic', () => {
		render(<StartForm onStart={() => undefined} loading={false} />)

		expect(screen.getByRole('button')).toBeDisabled()
	})

	it('uses suggestedTopic as the initial value', () => {
		render(<StartForm onStart={() => undefined} loading={false} suggestedTopic="Python basics" />)

		expect(screen.getByDisplayValue('Python basics')).toBeInTheDocument()
	})

	it('calls onStart with the topic', async () => {
		const onStart = vi.fn()
		const user = userEvent.setup()

		render(<StartForm onStart={onStart} loading={false} />)

		await user.type(screen.getByPlaceholderText(/What will you study/), 'Sorting algorithms')
		await user.click(screen.getByRole('button'))

		expect(onStart).toHaveBeenCalledWith('Sorting algorithms')
	})
})
