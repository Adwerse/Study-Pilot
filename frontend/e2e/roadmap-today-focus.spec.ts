import { expect, test } from '@playwright/test'
import { mockTelegram, resetTestData, seedTestData } from './helpers'

test.beforeEach(async ({ page }) => {
	await mockTelegram(page)
})

test('goal submission generates a deterministic roadmap', async ({ page, request }) => {
	await resetTestData(request)

	await page.goto('/roadmap')
	await page.getByLabel('What goal do you want to reach?').fill('Learn Python for automation testing')
	await page.getByRole('button', { name: 'Generate roadmap' }).click()

	await expect(page.getByText('Foundations')).toBeVisible()
	await expect(page.getByText('Guided Practice')).toBeVisible()
	await expect(page.getByText('Review And Ship')).toBeVisible()
})

test('today screen handles empty state and seeded focus tasks', async ({ page, request }) => {
	await resetTestData(request)
	await page.goto('/today')
	await expect(page.getByText('Start with a goal')).toBeVisible()

	await seedTestData(request, { with_plan: true })
	await page.reload()

	await expect(page.getByText('Focus blocks for today')).toBeVisible()
	await expect(page.getByText('Practice Foundations')).toBeVisible()
	await expect(page.getByText('Write learning notes')).toBeVisible()
})

test('focus session can start, stop, and appear in history', async ({ page, request }) => {
	await resetTestData(request)
	await seedTestData(request, { with_plan: true })

	await page.goto('/today')
	await page.getByRole('button', { name: 'Start' }).first().click()
	await page.getByRole('button', { name: 'Start session' }).click()

	await expect(page.getByText('Session running...')).toBeVisible()
	await page.getByRole('button', { name: 'Stop' }).click()
	await page.getByRole('button', { name: 'Difficulty 3' }).click()

	await page.getByRole('button', { name: 'History' }).click()
	await expect(page.getByText('Focus history')).toBeVisible()
	await expect(page.getByText('Foundations')).toBeVisible()
})
