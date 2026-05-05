import type { AxiosResponse } from 'axios'
import { afterEach, describe, expect, it, vi } from 'vitest'
import api, { apiClient } from './api'
import type { AskResponse, DocumentListResponse, DocumentUploadResponse } from '../types/api'

function makeResponse<T>(data: T): AxiosResponse<T> {
	return { data } as AxiosResponse<T>
}

describe('apiClient knowledge methods', () => {
	afterEach(() => {
		vi.restoreAllMocks()
	})

	it('getDocuments calls the documents endpoint with params', async () => {
		const response: DocumentListResponse = {
			items: [],
			total: 0,
			limit: 10,
			offset: 0,
		}
		const get = vi.spyOn(api, 'get').mockResolvedValue(makeResponse(response))
		const signal = new AbortController().signal

		await apiClient.getDocuments({ limit: 10, offset: 0, status: 'ready', q: 'notes' }, signal)

		expect(get).toHaveBeenCalledWith('/api/v1/documents', {
			params: { limit: 10, offset: 0, status: 'ready', q: 'notes' },
			signal,
		})
	})

	it('uploadDocument sends multipart form data', async () => {
		const response: DocumentUploadResponse = {
			document_id: 'doc-1',
			status: 'processing',
			title: 'Notes',
			filename: 'notes.txt',
			content_type: 'text/plain',
			size_bytes: 5,
			chunks_count: 0,
		}
		const post = vi.spyOn(api, 'post').mockResolvedValue(makeResponse(response))
		const file = new File(['hello'], 'notes.txt', { type: 'text/plain' })

		await apiClient.uploadDocument(file, {
			title: 'Notes',
			source_type: 'upload',
			tags: ['rag', 'study'],
		})

		const [url, body, config] = post.mock.calls[0]
		const form = body as FormData

		expect(url).toBe('/api/v1/documents/upload')
		expect(form).toBeInstanceOf(FormData)
		expect(form.get('file')).toBe(file)
		expect(form.get('title')).toBe('Notes')
		expect(form.get('source_type')).toBe('upload')
		expect(form.get('tags')).toBe('rag,study')
		expect(config?.headers).toEqual(expect.objectContaining({ 'Content-Type': 'multipart/form-data' }))
	})

	it('deleteDocument calls the document delete endpoint', async () => {
		const deleteRequest = vi.spyOn(api, 'delete').mockResolvedValue(makeResponse(undefined))
		const signal = new AbortController().signal

		await apiClient.deleteDocument('doc-1', signal)

		expect(deleteRequest).toHaveBeenCalledWith('/api/v1/documents/doc-1', { signal })
	})

	it('askQuestion sends question and selected document ids', async () => {
		const response: AskResponse = {
			answer: 'Answer [1].',
			confidence: 'high',
			rewritten_query: 'answer',
			sources: [],
		}
		const post = vi.spyOn(api, 'post').mockResolvedValue(makeResponse(response))
		const signal = new AbortController().signal

		await apiClient.askQuestion(
			{
				question: 'What is the deadline?',
				document_ids: ['doc-1'],
				top_k: 8,
				rerank_top_k: 4,
			},
			signal,
		)

		expect(post).toHaveBeenCalledWith(
			'/api/v1/ask',
			{
				question: 'What is the deadline?',
				document_ids: ['doc-1'],
				top_k: 8,
				rerank_top_k: 4,
			},
			{ signal },
		)
	})
})
