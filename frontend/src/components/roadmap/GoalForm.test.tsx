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
  it('кнопка задизейблена при пустой цели', () => {
    renderGoalForm()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('кнопка активна когда цель >= 10 символов', async () => {
    renderGoalForm()
    await userEvent.type(screen.getByPlaceholderText(/Например/), 'Выучить основы Python')
    expect(screen.getByRole('button')).not.toBeDisabled()
  })

  it('вызывает onSubmit с правильными параметрами', async () => {
    const onSubmit = vi.fn()
    renderGoalForm({ onSubmit })

    await userEvent.type(screen.getByPlaceholderText(/Например/), 'Выучить основы Python')
    await userEvent.click(screen.getByRole('button'))

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ goal: 'Выучить основы Python' }))
  })

  it('кнопка задизейблена при loading=true', () => {
    renderGoalForm({ loading: true })
    const textarea = screen.getByPlaceholderText(/Например/)
    expect(textarea).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })
})