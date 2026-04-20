import { apiClient } from '../lib/api'
import type { DailyPlan, FocusBlock, Plan } from '../types/api'
import { useApi } from './useApi'

interface LegacyTodayTask extends FocusBlock {
	id: string
	deliverable: string
}

export function usePlan() {
	const { data: plan, loading, error, refetch } = useApi<Plan | null>((signal) => apiClient.getCurrentPlan(signal))

	return { plan, loading, error, refetch }
}

export function useTodayTasks() {
	const { data, loading, error, refetch } = useApi<DailyPlan>((signal) => apiClient.getToday(signal))
	const tasks: LegacyTodayTask[] =
		data?.blocks.map((block, index) => ({
			...block,
			id: `${index}`,
			deliverable: block.description,
		})) ?? []

	return { tasks, loading, error, refetch }
}
