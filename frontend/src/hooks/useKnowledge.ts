import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiClient, normalizeApiError } from '../lib/api'
import type {
	ApiError,
	AskQuestionPayload,
	AskResponse,
	DocumentListParams,
	DocumentListResponse,
	DocumentUploadMetadata,
	DocumentUploadResponse,
	DocumentStatus,
	KnowledgeDocument,
} from '../types/api'

export interface UseDocumentsParams {
	limit?: number
	offset?: number
	status?: DocumentStatus
	q?: string
}

export interface UseDocumentsReturn {
	data: DocumentListResponse | null
	items: KnowledgeDocument[]
	total: number
	limit: number
	offset: number
	loading: boolean
	loadingMore: boolean
	error: ApiError | null
	hasMore: boolean
	refetch: () => void
	loadMore: () => void
}

interface DocumentsQuery {
	limit: number
	initialOffset: number
	pageOffset: number
	status?: DocumentStatus
	q?: string
	refreshIndex: number
}

function normalizeLimit(value: number | undefined): number {
	if (!Number.isFinite(value)) {
		return 20
	}

	return Math.min(100, Math.max(1, Math.round(value ?? 20)))
}

function normalizeOffset(value: number | undefined): number {
	if (!Number.isFinite(value)) {
		return 0
	}

	return Math.max(0, Math.round(value ?? 0))
}

function normalizeSearch(value: string | undefined): string | undefined {
	const normalized = value?.trim()
	return normalized ? normalized : undefined
}

function createDocumentsQuery(params: UseDocumentsParams): DocumentsQuery {
	const initialOffset = normalizeOffset(params.offset)

	return {
		limit: normalizeLimit(params.limit),
		initialOffset,
		pageOffset: initialOffset,
		status: params.status,
		q: normalizeSearch(params.q),
		refreshIndex: 0,
	}
}

function documentsQueryMatchesParams(query: DocumentsQuery, params: UseDocumentsParams): boolean {
	return (
		query.limit === normalizeLimit(params.limit) &&
		query.initialOffset === normalizeOffset(params.offset) &&
		query.status === params.status &&
		query.q === normalizeSearch(params.q)
	)
}

function appendUniqueDocuments(previous: KnowledgeDocument[], next: KnowledgeDocument[]): KnowledgeDocument[] {
	const seenIds = new Set(previous.map((item) => item.id))
	const uniqueNext = next.filter((item) => {
		if (seenIds.has(item.id)) {
			return false
		}

		seenIds.add(item.id)
		return true
	})

	return [...previous, ...uniqueNext]
}

function toDocumentListParams(query: DocumentsQuery): DocumentListParams {
	return {
		limit: query.limit,
		offset: query.pageOffset,
		status: query.status,
		q: query.q,
	}
}

export function useDocuments(params: UseDocumentsParams = {}): UseDocumentsReturn {
	const stableParams = useMemo(
		() => ({
			limit: params.limit,
			offset: params.offset,
			status: params.status,
			q: params.q,
		}),
		[params.limit, params.offset, params.q, params.status],
	)
	const [query, setQuery] = useState<DocumentsQuery>(() => createDocumentsQuery(stableParams))
	const [data, setData] = useState<DocumentListResponse | null>(null)
	const [items, setItems] = useState<KnowledgeDocument[]>([])
	const itemsRef = useRef<KnowledgeDocument[]>([])
	const [total, setTotal] = useState(0)
	const [responseLimit, setResponseLimit] = useState(query.limit)
	const [responseOffset, setResponseOffset] = useState(query.initialOffset)
	const [loading, setLoading] = useState(true)
	const [loadingMore, setLoadingMore] = useState(false)
	const [error, setError] = useState<ApiError | null>(null)

	useEffect(() => {
		setQuery((previous) => {
			if (documentsQueryMatchesParams(previous, stableParams)) {
				return previous
			}

			return createDocumentsQuery(stableParams)
		})
		setData(null)
		itemsRef.current = []
		setItems([])
		setTotal(0)
		setError(null)
	}, [stableParams])

	useEffect(() => {
		const controller = new AbortController()
		const isFirstPage = query.pageOffset === query.initialOffset

		if (isFirstPage) {
			setLoading(true)
		} else {
			setLoadingMore(true)
		}
		setError(null)

		apiClient
			.getDocuments(toDocumentListParams(query), controller.signal)
			.then((response) => {
				if (controller.signal.aborted) {
					return
				}

				const payload = response.data

				const nextItems = isFirstPage ? payload.items : appendUniqueDocuments(itemsRef.current, payload.items)

				itemsRef.current = nextItems
				setData({
					...payload,
					items: nextItems,
				})
				setItems(nextItems)
				setTotal(payload.total)
				setResponseLimit(payload.limit)
				setResponseOffset(payload.offset)
				setLoading(false)
				setLoadingMore(false)
			})
			.catch((documentsError) => {
				if (controller.signal.aborted) {
					return
				}

				setError(normalizeApiError(documentsError))
				setLoading(false)
				setLoadingMore(false)
			})

		return () => {
			controller.abort()
		}
	}, [query])

	const loadedThrough = query.initialOffset + items.length
	const hasMore = loadedThrough < total

	const refetch = useCallback(() => {
		setData(null)
		itemsRef.current = []
		setItems([])
		setQuery((previous) => ({
			...previous,
			pageOffset: previous.initialOffset,
			refreshIndex: previous.refreshIndex + 1,
		}))
	}, [])

	const loadMore = useCallback(() => {
		if (loading || loadingMore || !hasMore) {
			return
		}

		setQuery((previous) => ({
			...previous,
			pageOffset: responseOffset + responseLimit,
		}))
	}, [hasMore, loading, loadingMore, responseLimit, responseOffset])

	return {
		data,
		items,
		total,
		limit: responseLimit,
		offset: responseOffset,
		loading,
		loadingMore,
		error,
		hasMore,
		refetch,
		loadMore,
	}
}

export interface UseUploadDocumentReturn {
	uploading: boolean
	progress: number | null
	error: ApiError | null
	upload: (file: File, metadata?: DocumentUploadMetadata) => Promise<DocumentUploadResponse>
	reset: () => void
}

export function useUploadDocument(onSuccess?: (document: DocumentUploadResponse) => void): UseUploadDocumentReturn {
	const [uploading, setUploading] = useState(false)
	const [progress, setProgress] = useState<number | null>(null)
	const [error, setError] = useState<ApiError | null>(null)

	const reset = useCallback(() => {
		setProgress(null)
		setError(null)
	}, [])

	const upload = useCallback(
		async (file: File, metadata: DocumentUploadMetadata = {}) => {
			setUploading(true)
			setProgress(0)
			setError(null)

			try {
				const response = await apiClient.uploadDocument(file, metadata, {
					onUploadProgress: (event) => {
						if (!event.total) {
							return
						}

						setProgress(Math.min(100, Math.round((event.loaded / event.total) * 100)))
					},
				})

				setProgress(100)
				onSuccess?.(response.data)
				return response.data
			} catch (uploadError) {
				const normalized = normalizeApiError(uploadError)
				setError(normalized)
				throw normalized
			} finally {
				setUploading(false)
			}
		},
		[onSuccess],
	)

	return {
		uploading,
		progress,
		error,
		upload,
		reset,
	}
}

export interface UseDeleteDocumentReturn {
	deletingIds: Set<string>
	error: ApiError | null
	isDeleting: (documentId: string) => boolean
	deleteDocument: (documentId: string) => Promise<void>
	clearError: () => void
}

export function useDeleteDocument(onSuccess?: (documentId: string) => void): UseDeleteDocumentReturn {
	const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())
	const [error, setError] = useState<ApiError | null>(null)

	const isDeleting = useCallback((documentId: string) => deletingIds.has(documentId), [deletingIds])

	const clearError = useCallback(() => {
		setError(null)
	}, [])

	const deleteDocument = useCallback(
		async (documentId: string) => {
			setDeletingIds((previous) => new Set(previous).add(documentId))
			setError(null)

			try {
				await apiClient.deleteDocument(documentId)
				onSuccess?.(documentId)
			} catch (deleteError) {
				const normalized = normalizeApiError(deleteError)
				setError(normalized)
				throw normalized
			} finally {
				setDeletingIds((previous) => {
					const next = new Set(previous)
					next.delete(documentId)
					return next
				})
			}
		},
		[onSuccess],
	)

	return {
		deletingIds,
		error,
		isDeleting,
		deleteDocument,
		clearError,
	}
}

export interface UseAskQuestionReturn {
	loading: boolean
	error: ApiError | null
	ask: (question: string, options?: Omit<AskQuestionPayload, 'question'>) => Promise<AskResponse>
	clearError: () => void
}

export function useAskQuestion(): UseAskQuestionReturn {
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<ApiError | null>(null)

	const clearError = useCallback(() => {
		setError(null)
	}, [])

	const ask = useCallback(async (question: string, options: Omit<AskQuestionPayload, 'question'> = {}) => {
		setLoading(true)
		setError(null)

		try {
			const response = await apiClient.askQuestion({
				...options,
				question,
			})
			return response.data
		} catch (askError) {
			const normalized = normalizeApiError(askError)
			setError(normalized)
			throw normalized
		} finally {
			setLoading(false)
		}
	}, [])

	return {
		loading,
		error,
		ask,
		clearError,
	}
}
