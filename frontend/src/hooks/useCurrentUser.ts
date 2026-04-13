import { useEffect, useState } from 'react'
import api from '../lib/api'

interface TelegramUser {
  id: number
  username?: string
  first_name: string
}

interface CurrentUserApiResponse {
  id?: number
  telegram_id?: number
  username?: string
  first_name?: string
}

export function useCurrentUser() {
  const [user, setUser] = useState<TelegramUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get('/api/v1/users/me')
      .then((res) => {
        const payload = res.data as CurrentUserApiResponse
        if (!payload || typeof payload !== 'object' || !payload.first_name) {
          throw new Error('Invalid current user payload')
        }

        const id = payload.id ?? payload.telegram_id
        if (typeof id !== 'number') {
          throw new Error('Missing user id')
        }

        setUser({
          id,
          username: payload.username,
          first_name: payload.first_name,
        })
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return { user, loading, error }
}