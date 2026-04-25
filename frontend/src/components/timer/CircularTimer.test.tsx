import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CircularTimer } from './CircularTimer'

describe('CircularTimer', () => {
	it('renders time in MM:SS format', () => {
		render(<CircularTimer remaining={25 * 60} progress={0} status="idle" />)

		expect(screen.getByText('25:00')).toBeInTheDocument()
	})

	it('renders remaining time correctly', () => {
		render(<CircularTimer remaining={90} progress={0.94} status="running" />)

		expect(screen.getByText('01:30')).toBeInTheDocument()
	})

	it('shows "done!" when finished', () => {
		render(<CircularTimer remaining={0} progress={1} status="finished" />)

		expect(screen.getByText('done!')).toBeInTheDocument()
	})

	it('shows "remaining" when running', () => {
		render(<CircularTimer remaining={90} progress={0.94} status="running" />)

		expect(screen.getByText('remaining')).toBeInTheDocument()
	})
})
