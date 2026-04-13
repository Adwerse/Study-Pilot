import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { expandApp, ready } from './lib/telegram'
import { useCurrentUser } from './hooks/useCurrentUser'

ready()
expandApp()

function App() {
	const { user, loading, error } = useCurrentUser()

	if (loading) {
		return <div>Загрузка...</div>
	}

	if (error) {
		return <div>Ошибка: {error}</div>
	}

	if (!user) {
		return <div>Пользователь не найден</div>
	}

	return (
		<div>
			Привет, {user.first_name}! id: {user.id}
		</div>
	)
}

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<App />
	</StrictMode>,
)
