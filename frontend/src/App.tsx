import { useEffect } from 'react'
import { expand, getTelegramUser, ready } from './lib/telegram'

export default function App() {
	useEffect(() => {
		ready()
		expand()
	}, [])

	const user = getTelegramUser()

	return (
		<main style={{ fontFamily: 'sans-serif', padding: '16px' }}>
			<h1>Learning OS</h1>
			<p>{user ? `Hello, ${user.first_name ?? 'friend'}` : 'Dev mode: no Telegram user'}</p>
			<small>API: {import.meta.env.VITE_API_BASE_URL}</small>
		</main>
	)
}
