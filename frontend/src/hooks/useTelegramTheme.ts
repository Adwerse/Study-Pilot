import { useEffect, useState } from 'react'

type ThemeParams = Record<string, string>

type TelegramWebApp = {
	themeParams?: ThemeParams
	colorScheme?: 'light' | 'dark'
	onEvent?: (event: 'themeChanged', handler: () => void) => void
	offEvent?: (event: 'themeChanged', handler: () => void) => void
}

const THEME_PARAM_TO_CSS_VAR: Record<string, string> = {
	bg_color: '--tg-theme-bg-color',
	secondary_bg_color: '--tg-theme-secondary-bg-color',
	text_color: '--tg-theme-text-color',
	hint_color: '--tg-theme-hint-color',
	link_color: '--tg-theme-link-color',
	button_color: '--tg-theme-button-color',
	button_text_color: '--tg-theme-button-text-color',
}

function applyThemeParams(themeParams: ThemeParams) {
	const root = document.documentElement

	for (const [telegramParam, cssVar] of Object.entries(THEME_PARAM_TO_CSS_VAR)) {
		const value = themeParams[telegramParam]
		if (value) {
			root.style.setProperty(cssVar, value)
		}
	}
}

export function useTelegramTheme(): { isDark: boolean; themeParams: ThemeParams | null } {
	const [isDark, setIsDark] = useState(false)
	const [themeParams, setThemeParams] = useState<ThemeParams | null>(null)

	useEffect(() => {
		const webApp = (window as Window & { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp

		if (!webApp) {
			setIsDark(false)
			setThemeParams(null)
			return
		}

		const syncTheme = () => {
			const nextThemeParams = webApp.themeParams ?? null

			if (nextThemeParams) {
				applyThemeParams(nextThemeParams)
			}

			setThemeParams(nextThemeParams)
			setIsDark(webApp.colorScheme === 'dark')
		}

		syncTheme()
		webApp.onEvent?.('themeChanged', syncTheme)

		return () => {
			webApp.offEvent?.('themeChanged', syncTheme)
		}
	}, [])

	return {
		isDark,
		themeParams,
	}
}
