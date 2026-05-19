import { expect, test } from '@playwright/test'
import { apiBaseURL, authHeaders, buildTelegramInitData, mockTelegram, resetTestData, seedTestData } from './helpers'

test.beforeEach(async ({ page }) => {
	await mockTelegram(page)
})

test('knowledge base uploads a text file and lists it', async ({ page, request }) => {
	await resetTestData(request)

	await page.goto('/knowledge')
	await page.locator('input[type="file"]').setInputFiles({
		name: 'study-notes.txt',
		mimeType: 'text/plain',
		buffer: Buffer.from('Focus loops connect goals, sessions, notes, and review.'),
	})
	await page.locator('button').first().click()

	await expect(page.getByText('study-notes.txt')).toBeVisible()
	await expect(page.getByText('study-notes')).toBeVisible()
})

test('rag chat renders an answer with sources and a no-source state', async ({ page, request }) => {
	await resetTestData(request)
	await seedTestData(request, { with_documents: true })

	await page.goto('/knowledge')
	await page.getByRole('tab').nth(1).click()
	await page.locator('textarea').fill('What do the notes say about focus loops?')
	await page.locator('textarea').press('Enter')

	await expect(page.getByText(/focus loops connect goals/i)).toBeVisible()
	await expect(page.getByText('Focus Notes')).toBeVisible()

	await resetTestData(request)
	await page.reload()
	await page.getByRole('tab').nth(1).click()
	await expect(page.locator('textarea')).toBeDisabled()
})

test('analytics renders empty and seeded data states without chart crashes', async ({ page, request }) => {
	await resetTestData(request)

	await page.goto('/analytics')
	await expect(page.locator('.analytics-summary-grid')).toBeVisible()
	await expect(page.locator('.analytics-heatmap-grid')).toBeVisible()

	await seedTestData(request, { with_plan: true, with_analytics: true })
	await page.reload()

	await expect(page.locator('.analytics-summary-grid')).toBeVisible()
	await expect(page.getByText('RAG')).toBeVisible()
})

test('weekly review generate, apply, and history work through protected API', async ({ request }) => {
	await resetTestData(request)
	await seedTestData(request, { with_plan: true, with_analytics: true })
	const initData = buildTelegramInitData()

	const generateResponse = await request.post(`${apiBaseURL}/api/v1/weekly-review/generate`, {
		headers: authHeaders(initData),
		data: { timezone: 'UTC', apply_changes: false },
	})
	expect(generateResponse.ok()).toBeTruthy()
	const generated = await generateResponse.json()
	expect(generated.status).toBe('draft')
	expect(generated.proposed_changes).toBeDefined()

	const applyResponse = await request.post(`${apiBaseURL}/api/v1/weekly-review/${generated.review_id}/apply`, {
		headers: authHeaders(initData),
	})
	expect(applyResponse.ok()).toBeTruthy()
	expect((await applyResponse.json()).status).toBe('applied')

	const historyResponse = await request.get(`${apiBaseURL}/api/v1/weekly-review/history`, {
		headers: authHeaders(initData),
	})
	expect(historyResponse.ok()).toBeTruthy()
	const history = await historyResponse.json()
	expect(history.total).toBeGreaterThanOrEqual(1)
})
