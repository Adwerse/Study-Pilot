import { apiClient } from '../lib/api'
import type { User } from '../types/api'
import { useApi } from './useApi'

export function useCurrentUser() {
	const { data: user, loading, error, refetch } = useApi<User>((signal) => apiClient.getMe(signal))

	return { user, loading, error, refetch }
}