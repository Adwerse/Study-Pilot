import { act, renderHook, waitFor } from '@testing-library/react'
import type { AxiosResponse } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '../lib/api'
import type { AskResponse, DocumentListResponse, DocumentUploadResponse, KnowledgeDocument } from '../types/api'
import { useAskQuestion, useDeleteDocument, useDocuments, useUploadDocument } from './useKnowledge'

function makeResponse<T>(data: T): AxiosResponse<T> {
	return { data } as AxiosResponse<T>
}

function makeDocument(overrides: Partial<KnowledgeDocument> = {}): KnowledgeDocument {
	return {
		id: 'doc-1',
		title: 'Notes',
		filename: 'notes.txt',
		content_type: 'text/plain',
		size_bytes: 1024,
		status: 'ready',
		chunks_count: 2,
		error_message: null,
		created_at: '2026-05-01T10:00:00Z',
		updated_at: '2026-05-01T10:00:00Z',
		...overrides,
	}
}

describe('knowledge hooks', () => {
	afterEach(() => {
		vi.restoreAllMocks()
	})

	it('useDocuments loads more and appends documents', async () => {
		const getDocuments = vi.spyOn(apiClient, 'getDocuments')
		getDocuments
			.mockResolvedValueOnce(
				makeResponse<DocumentListResponse>({
					items: [makeDocument({ id: 'doc-1' })],
					total: 2,
					limit: 1,
					offset: 0,
				}),
			)
			.mockResolvedValueOnce(
				makeResponse<DocumentListResponse>({
					items: [makeDocument({ id: 'doc-2', title: 'Roadmap', filename: 'roadmap.pdf' })],
					total: 2,
					limit: 1,
					offset: 1,
				}),
			)

		const { result } = renderHook(() => useDocuments({ limit: 1, status: 'ready' }))

		await waitFor(() => expect(result.current.loading).toBe(false))
		expect(result.current.items).toHaveLength(1)

		act(() => {
			result.current.loadMore()
		})

		await waitFor(() => expect(result.current.items).toHaveLength(2))
		expect(getDocuments).toHaveBeenNthCalledWith(
			1,
			expect.objectContaining({ limit: 1, offset: 0, status: 'ready' }),
			expect.any(AbortSignal),
		)
		expect(getDocuments).toHaveBeenNthCalledWith(
			2,
			expect.objectContaining({ limit: 1, offset: 1, status: 'ready' }),
			expect.any(AbortSignal),
		)
	})

	it('useUploadDocument calls upload and success callback', async () => {
		const uploadResponse: DocumentUploadResponse = {
			document_id: 'doc-1',
			status: 'ready',
			title: 'Notes',
			filename: 'notes.txt',
			content_type: 'text/plain',
			size_bytes: 5,
			chunks_count: 1,
		}
		const uploadDocument = vi.spyOn(apiClient, 'uploadDocument').mockResolvedValue(makeResponse(uploadResponse))
		const onSuccess = vi.fn()
		const file = new File(['hello'], 'notes.txt', { type: 'text/plain' })

		const { result } = renderHook(() => useUploadDocument(onSuccess))

		await act(async () => {
			await result.current.upload(file, { title: 'Notes' })
		})

		expect(uploadDocument).toHaveBeenCalledWith(
			file,
			{ title: 'Notes' },
			expect.objectContaining({ onUploadProgress: expect.any(Function) }),
		)
		expect(onSuccess).toHaveBeenCalledWith(uploadResponse)
		expect(result.current.progress).toBe(100)
	})

	it('useDeleteDocument calls delete endpoint and success callback', async () => {
		const deleteRequest = vi.spyOn(apiClient, 'deleteDocument').mockResolvedValue(makeResponse(undefined))
		const onSuccess = vi.fn()
		const { result } = renderHook(() => useDeleteDocument(onSuccess))

		await act(async () => {
			await result.current.deleteDocument('doc-1')
		})

		expect(deleteRequest).toHaveBeenCalledWith('doc-1')
		expect(onSuccess).toHaveBeenCalledWith('doc-1')
		expect(result.current.isDeleting('doc-1')).toBe(false)
	})

	it('useAskQuestion sends question and selected documents', async () => {
		const askResponse: AskResponse = {
			answer: 'Answer [1].',
			confidence: 'high',
			rewritten_query: 'answer',
			sources: [],
		}
		const askQuestion = vi.spyOn(apiClient, 'askQuestion').mockResolvedValue(makeResponse(askResponse))
		const { result } = renderHook(() => useAskQuestion())

		await act(async () => {
			await result.current.ask('What is inside?', { document_ids: ['doc-1'] })
		})

		expect(askQuestion).toHaveBeenCalledWith({
			question: 'What is inside?',
			document_ids: ['doc-1'],
		})
	})
})
