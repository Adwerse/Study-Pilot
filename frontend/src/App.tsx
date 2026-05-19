import { useEffect } from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useTelegramTheme } from './hooks/useTelegramTheme'
import { expand, ready, subscribeViewportChanges, syncViewportCssVars } from './lib/telegram'
import { AppRouter } from './router'

export default function App() {
	useTelegramTheme()

	useEffect(() => {
		ready()
		expand()
		syncViewportCssVars()
		return subscribeViewportChanges(syncViewportCssVars)
	}, [])

	return (
		<ErrorBoundary>
			<AppRouter />
		</ErrorBoundary>
	)
}
