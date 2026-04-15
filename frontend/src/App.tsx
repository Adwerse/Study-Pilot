import { useEffect } from 'react'
import { useTelegramTheme } from './hooks/useTelegramTheme'
import { expand, ready } from './lib/telegram'
import { AppRouter } from './router'

export default function App() {
	useTelegramTheme()

	useEffect(() => {
		ready()
		expand()
	}, [])

	return <AppRouter />
}
