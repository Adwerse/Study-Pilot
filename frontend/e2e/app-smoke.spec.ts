import { expect, test } from '@playwright/test'
import { apiBaseURL, authHeaders, buildTelegramInitData, mockTelegram, resetTestData } from './helpers'

test.beforeEach(async ({ page }) => {
	await mockTelegram(page)
})

test('app loads with Telegram mock and visible navigation', async ({ page, request }) => {
	await resetTestData(request)

	await page.goto('/')

	await expect(page).toHaveURL(/\/today$/)
	await expect(page.getByText('Start with a goal')).toBeVisible()
	await expect(page.locator('a[href="/today"]')).toBeVisible()
	await expect(page.locator('a[href="/roadmap"]')).toBeVisible()
	await expect(page.locator('a[href="/knowledge"]')).toBeVisible()
	await expect(page.locator('a[href="/analytics"]')).toBeVisible()
})

test('auth bootstrap accepts signed Telegram initData for protected APIs', async ({ request }) => {
	await resetTestData(request)
	const initData = buildTelegramInitData()

	const meResponse = await request.get(`${apiBaseURL}/api/v1/users/me`, {
		headers: authHeaders(initData),
	})

	expect(meResponse.ok()).toBeTruthy()
	expect(await meResponse.json()).toMatchObject({
		telegram_id: 777001,
		username: 'e2e_tester',
		first_name: 'E2E',
	})
})
