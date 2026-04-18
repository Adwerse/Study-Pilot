import { useCallback, useEffect, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type { Plan } from '../types/api'

export type RoadmapScreenState = 'empty' | 'generating' | 'result' | 'error'

export interface GenerateParams {
  goal: string
  level: 'beginner' | 'intermediate' | 'advanced'
  weekly_hours: number
  deadline?: string
}

export interface UseRoadmapReturn {
  state: RoadmapScreenState
  plan: Plan | null
  error: string | null
  generate: (params: GenerateParams) => Promise<void>
  reset: () => void
}

export function useRoadmap(): UseRoadmapReturn {
  const [state, setState] = useState<RoadmapScreenState>('empty')
  const [plan, setPlan] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    apiClient
      .getCurrentPlan(controller.signal)
      .then((response) => {
        const currentPlan = response.data

        if (currentPlan) {
          setPlan(currentPlan)
          setState('result')
          return
        }

        setPlan(null)
        setError(null)
        setState('empty')
      })
      .catch((requestError) => {
        const normalized = normalizeApiError(requestError)

        if (normalized.status === 404) {
          setPlan(null)
          setError(null)
          setState('empty')
          return
        }

        setPlan(null)
        setError(normalized.detail)
        setState('error')
      })

    return () => {
      controller.abort()
    }
  }, [])

  const generate = useCallback(async (params: GenerateParams) => {
    setState('generating')
    setError(null)

    try {
      const response = await apiClient.createPlan(params.goal, params)
      setPlan(response.data)
      setState('result')
    } catch (requestError) {
      const normalized = normalizeApiError(requestError)
      setPlan(null)
      setError(normalized.detail)
      setState('error')
    }
  }, [])

  const reset = useCallback(() => {
    setState('empty')
    setPlan(null)
    setError(null)
  }, [])

  return {
    state,
    plan,
    error,
    generate,
    reset,
  }
}