import { useEffect } from 'react'
import { useTelegramTheme } from './hooks/useTelegramTheme'
import { expand, ready } from './lib/telegram'
import { DevKit } from './pages/DevKit'

export default function App() {
	useTelegramTheme()

	useEffect(() => {
		ready()
		expand()
	}, [])

	return <DevKit />
}
