import crypto from 'node:crypto'
import { APIRequestContext, Page, expect } from '@playwright/test'

export const apiBaseURL = process.env.E2E_API_BASE_URL ?? 'http://127.0.0.1:8000'
export const e2eSecret = process.env.E2E_TEST_SECRET ?? 'studypilot-e2e-secret'
export const botToken = process.env.BOT_TOKEN ?? '123456:TEST_TOKEN'
export const testUser = {
	id: 777001,
	username: 'e2e_tester',
	first_name: 'E2E',
}

export function buildTelegramInitData(user = testUser): string {
	const data: Record<string, string> = {
		auth_date: '1770000000',
		query_id: 'AAE2ZTcQAAAAADZlNxAAAAAA',
		user: JSON.stringify(user),
	}
	const dataCheckString = Object.keys(data)
		.sort()
		.map((key) => `${key}=${data[key]}`)
		.join('\n')
	const secretKey = crypto.createHmac('sha256', 'WebAppData').update(botToken).digest()
	const hash = crypto.createHmac('sha256', secretKey).update(dataCheckString).digest('hex')
	return new URLSearchParams({ ...data, hash }).toString()
}

export async function mockTelegram(page: Page, initData = buildTelegramInitData()) {
	await page.addInitScript(
		({ providedInitData, user }) => {
			window.Telegram = {
				WebApp: {
					initData: providedInitData,
					initDataUnsafe: { user },
					colorScheme: 'light',
					themeParams: {
						bg_color: '#ffffff',
						secondary_bg_color: '#f4f4f5',
						text_color: '#111827',
						hint_color: '#6b7280',
						button_color: '#2563eb',
						button_text_color: '#ffffff',
					},
					viewportHeight: 844,
					viewportStableHeight: 844,
					ready: () => undefined,
					expand: () => undefined,
					close: () => {
						window.__telegramClosed = true
					},
					onEvent: () => undefined,
					offEvent: () => undefined,
				},
			}
		},
		{ providedInitData: initData, user: testUser },
	)
}

export async function resetTestData(request: APIRequestContext) {
	const response = await request.post(`${apiBaseURL}/api/v1/test/reset`, {
		headers: { 'X-Test-Secret': e2eSecret },
	})
	expect(response.ok()).toBeTruthy()
}

export async function seedTestData(
	request: APIRequestContext,
	options: Record<string, boolean | number> = {},
) {
	const response = await request.post(`${apiBaseURL}/api/v1/test/seed`, {
		headers: { 'X-Test-Secret': e2eSecret },
		data: {
			telegram_id: testUser.id,
			...options,
		},
	})
	expect(response.ok()).toBeTruthy()
	return response.json()
}

export function authHeaders(initData = buildTelegramInitData()) {
	return {
		Authorization: `tma ${initData}`,
	}
}

declare global {
	interface Window {
		Telegram?: unknown
		__telegramClosed?: boolean
	}
}
