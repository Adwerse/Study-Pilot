import { apiClient } from '../lib/api'
import type { Plan, PlanStage } from '../types/api'
import { useApi } from './useApi'

type TodayTasksResponse = PlanStage[] | { tasks: PlanStage[] }

function extractTasks(response: TodayTasksResponse | null): PlanStage[] {
	if (!response) {
		return []
	}

	if (Array.isArray(response)) {
		return response
	}

	if (Array.isArray(response.tasks)) {
		return response.tasks
	}

	return []
}

export function usePlan() {
	const { data: plan, loading, error, refetch } = useApi<Plan | null>((signal) => apiClient.getCurrentPlan(signal))

	return { plan, loading, error, refetch }
}

export function useTodayTasks() {
	const { data, loading, error, refetch } = useApi<TodayTasksResponse>((signal) => apiClient.getToday(signal))
	const tasks = extractTasks(data)

	return { tasks, loading, error, refetch }
}
