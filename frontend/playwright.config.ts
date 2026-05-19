import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173'

export default defineConfig({
	testDir: './e2e',
	fullyParallel: false,
	workers: 1,
	retries: process.env.CI ? 2 : 0,
	reporter: process.env.CI ? [['html', { open: 'never' }], ['github']] : 'list',
	use: {
		baseURL,
		trace: 'on-first-retry',
		screenshot: 'only-on-failure',
		video: 'retain-on-failure',
		...devices['Pixel 5'],
		viewport: { width: 390, height: 844 },
	},
	webServer: {
		command: 'npm run dev -- --host 127.0.0.1 --port 5173',
		url: baseURL,
		reuseExistingServer: !process.env.CI,
		timeout: 120_000,
	},
})
