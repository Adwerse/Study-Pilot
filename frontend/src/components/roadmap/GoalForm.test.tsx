import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { GoalForm } from './GoalForm'

function renderGoalForm(options?: { loading?: boolean; onSubmit?: (params: unknown) => void }) {
  const onSubmit = options?.onSubmit ?? vi.fn()

  render(<GoalForm onSubmit={onSubmit as never} loading={options?.loading ?? false} />)

  return { onSubmit }
}

describe('GoalForm', () => {
  it('disables the button when the goal is empty', () => {
    renderGoalForm()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('enables the button when the goal has at least 10 characters', async () => {
    renderGoalForm()
    await userEvent.type(screen.getByPlaceholderText(/For example/), 'Learn Python fundamentals')
    expect(screen.getByRole('button')).not.toBeDisabled()
  })

  it('calls onSubmit with the correct parameters', async () => {
    const onSubmit = vi.fn()
    renderGoalForm({ onSubmit })

    await userEvent.type(screen.getByPlaceholderText(/For example/), 'Learn Python fundamentals')
    await userEvent.click(screen.getByRole('button'))

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ goal: 'Learn Python fundamentals' }))
  })

  it('disables the button when loading=true', () => {
    renderGoalForm({ loading: true })
    const textarea = screen.getByPlaceholderText(/For example/)
    expect(textarea).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
