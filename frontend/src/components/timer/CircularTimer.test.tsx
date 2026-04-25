import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CircularTimer } from './CircularTimer'

describe('CircularTimer', () => {
	it('отображает время в формате MM:SS', () => {
		render(<CircularTimer remaining={25 * 60} progress={0} status="idle" />)

		expect(screen.getByText('25:00')).toBeInTheDocument()
	})

	it('отображает оставшееся время корректно', () => {
		render(<CircularTimer remaining={90} progress={0.94} status="running" />)

		expect(screen.getByText('01:30')).toBeInTheDocument()
	})

	it('показывает "готово!" при finished', () => {
		render(<CircularTimer remaining={0} progress={1} status="finished" />)

		expect(screen.getByText('готово!')).toBeInTheDocument()
	})

	it('показывает "осталось" при running', () => {
		render(<CircularTimer remaining={90} progress={0.94} status="running" />)

		expect(screen.getByText('осталось')).toBeInTheDocument()
	})
})
