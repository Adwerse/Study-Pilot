import '@testing-library/jest-dom/vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useAskQuestion, useDeleteDocument, useDocuments, useUploadDocument } from '../hooks'
import type {
	UseAskQuestionReturn,
	UseDeleteDocumentReturn,
	UseDocumentsReturn,
	UseUploadDocumentReturn,
} from '../hooks/useKnowledge'
import type { AskResponse, DocumentUploadResponse, KnowledgeDocument } from '../types/api'
import { KnowledgeBaseScreen } from './KnowledgePage'

vi.mock('../hooks', () => ({
	useAskQuestion: vi.fn(),
	useDeleteDocument: vi.fn(),
	useDocuments: vi.fn(),
	useUploadDocument: vi.fn(),
}))

const useDocumentsMock = vi.mocked(useDocuments)
const useUploadDocumentMock = vi.mocked(useUploadDocument)
const useDeleteDocumentMock = vi.mocked(useDeleteDocument)
const useAskQuestionMock = vi.mocked(useAskQuestion)

function makeDocument(overrides: Partial<KnowledgeDocument> = {}): KnowledgeDocument {
	return {
		id: 'doc-ready',
		title: 'Roadmap',
		filename: 'roadmap.pdf',
		content_type: 'application/pdf',
		size_bytes: 1_048_576,
		status: 'ready',
		chunks_count: 4,
		error_message: null,
		created_at: '2026-05-01T10:00:00Z',
		updated_at: '2026-05-01T10:05:00Z',
		...overrides,
	}
}

function mockDocuments(overrides: Partial<UseDocumentsReturn> = {}) {
	const state: UseDocumentsReturn = {
		data: null,
		items: [],
		total: 0,
		limit: 10,
		offset: 0,
		loading: false,
		loadingMore: false,
		error: null,
		hasMore: false,
		refetch: vi.fn(),
		loadMore: vi.fn(),
		...overrides,
	}

	useDocumentsMock.mockReturnValue(state)
	return state
}

function mockUpload(uploadResponse?: DocumentUploadResponse) {
	let onSuccessHandler: ((document: DocumentUploadResponse) => void) | undefined
	const response: DocumentUploadResponse =
		uploadResponse ??
		{
			document_id: 'doc-uploaded',
			status: 'ready',
			title: 'Notes',
			filename: 'notes.txt',
			content_type: 'text/plain',
			size_bytes: 5,
			chunks_count: 1,
		}
	const upload = vi.fn(async () => {
		onSuccessHandler?.(response)
		return response
	})
	const reset = vi.fn()

	useUploadDocumentMock.mockImplementation((onSuccess) => {
		onSuccessHandler = onSuccess

		return {
			uploading: false,
			progress: null,
			error: null,
			upload,
			reset,
		}
	})

	return { upload, reset }
}

function mockDelete() {
	let onSuccessHandler: ((documentId: string) => void) | undefined
	const deleteDocument = vi.fn(async (documentId: string) => {
		onSuccessHandler?.(documentId)
	})

	useDeleteDocumentMock.mockImplementation((onSuccess) => {
		onSuccessHandler = onSuccess

		return {
			deletingIds: new Set<string>(),
			error: null,
			isDeleting: () => false,
			deleteDocument,
			clearError: vi.fn(),
		}
	})

	return deleteDocument
}

function mockAsk(overrides: Partial<UseAskQuestionReturn> = {}) {
	const answer: AskResponse = {
		answer: 'Ответ из roadmap [1].',
		confidence: 'high',
		rewritten_query: 'roadmap',
		sources: [
			{
				document_id: 'doc-ready',
				document_title: 'Roadmap',
				filename: 'roadmap.pdf',
				chunk_id: 'chunk-1',
				chunk_index: 0,
				score: 0.91,
				page_number: 3,
				snippet: 'Submit the project by Friday.',
			},
		],
	}
	const state: UseAskQuestionReturn = {
		loading: false,
		error: null,
		ask: vi.fn(async () => answer),
		clearError: vi.fn(),
		...overrides,
	}

	useAskQuestionMock.mockReturnValue(state)
	return state
}

function setupBaseMocks(documentsOverride: Partial<UseDocumentsReturn> = {}) {
	const documents = mockDocuments(documentsOverride)
	mockUpload()
	const deleteDocument = mockDelete()
	const ask = mockAsk()

	return { documents, deleteDocument, ask }
}

describe('KnowledgeBaseScreen', () => {
	afterEach(() => {
		vi.restoreAllMocks()
		vi.clearAllMocks()
	})

	it('renders empty documents state', () => {
		setupBaseMocks()

		render(<KnowledgeBaseScreen />)

		expect(screen.getByText('Пока нет материалов')).toBeInTheDocument()
		expect(screen.getByText('Загрузи PDF, TXT или MD — и StudyPilot сможет отвечать по ним.')).toBeInTheDocument()
	})

	it('renders documents list with processing, ready and failed badges', () => {
		setupBaseMocks({
			items: [
				makeDocument(),
				makeDocument({ id: 'doc-processing', title: 'Draft', filename: 'draft.md', status: 'processing', chunks_count: 0 }),
				makeDocument({
					id: 'doc-failed',
					title: 'Broken',
					filename: 'broken.txt',
					status: 'failed',
					chunks_count: 0,
					error_message: 'Document processing failed',
				}),
			],
			total: 3,
		})

		render(<KnowledgeBaseScreen />)

		expect(screen.getByText('Roadmap')).toBeInTheDocument()
		expect(screen.getAllByText('Обработка').length).toBeGreaterThan(0)
		expect(screen.getAllByText('Готов').length).toBeGreaterThan(0)
		expect(screen.getAllByText('Ошибка').length).toBeGreaterThan(0)
		expect(screen.getByText('Document processing failed')).toBeInTheDocument()
	})

	it('refreshes documents after upload success', async () => {
		const user = userEvent.setup()
		const documents = mockDocuments()
		const { upload } = mockUpload()
		mockDelete()
		mockAsk()

		render(<KnowledgeBaseScreen />)

		await user.upload(screen.getByLabelText('Файл материала'), new File(['hello'], 'notes.txt', { type: 'text/plain' }))
		await user.click(screen.getByRole('button', { name: 'Загрузить' }))

		await waitFor(() => expect(upload).toHaveBeenCalledTimes(1))
		expect(documents.refetch).toHaveBeenCalledTimes(1)
		expect(screen.getByText('Материал готов к чату')).toBeInTheDocument()
	})

	it('asks for confirmation before deleting a document', async () => {
		const user = userEvent.setup()
		const { deleteDocument } = setupBaseMocks({
			items: [makeDocument()],
			total: 1,
		})
		const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)

		render(<KnowledgeBaseScreen />)

		await user.click(screen.getByRole('button', { name: 'Удалить' }))

		expect(confirm).toHaveBeenCalledWith('Удалить материал? Ответы по нему больше не будут доступны.')
		expect(deleteDocument).toHaveBeenCalledWith('doc-ready')
	})

	it('disables chat when there are no ready documents', async () => {
		const user = userEvent.setup()
		setupBaseMocks()

		render(<KnowledgeBaseScreen />)

		await user.click(screen.getByRole('tab', { name: 'Чат' }))

		expect(screen.getByText('Сначала загрузи материал, потом можно будет задавать вопросы.')).toBeInTheDocument()
		expect(screen.getByLabelText('Вопрос')).toBeDisabled()
		expect(screen.getByRole('button', { name: 'Отправить' })).toBeDisabled()
	})

	it('sends a question and renders assistant answer with sources', async () => {
		const user = userEvent.setup()
		const { ask } = setupBaseMocks({
			items: [makeDocument()],
			total: 1,
		})

		render(<KnowledgeBaseScreen />)

		await user.click(screen.getByRole('tab', { name: 'Чат' }))
		await user.type(screen.getByLabelText('Вопрос'), 'Когда дедлайн?')
		await user.click(screen.getByRole('button', { name: 'Отправить' }))

		expect(ask.ask).toHaveBeenCalledWith('Когда дедлайн?', { document_ids: undefined })
		expect(await screen.findByText('Когда дедлайн?')).toBeInTheDocument()
		expect(await screen.findByText('Ответ из roadmap [1].')).toBeInTheDocument()
		expect(screen.getByText('Источники')).toBeInTheDocument()
		expect(screen.getByText(/\[1\] Roadmap · стр\. 3/)).toBeInTheDocument()
		expect(screen.getByText('"Submit the project by Friday."')).toBeInTheDocument()
	})

	it('shows ask errors as human text', async () => {
		const user = userEvent.setup()
		mockDocuments({ items: [makeDocument()], total: 1 })
		mockUpload()
		mockDelete()
		mockAsk({
			ask: vi.fn(async () => {
				throw { detail: 'RAG service is temporarily unavailable', status: 503 }
			}),
		})

		render(<KnowledgeBaseScreen />)

		await user.click(screen.getByRole('tab', { name: 'Чат' }))
		await user.type(screen.getByLabelText('Вопрос'), 'Что внутри?')
		await user.click(screen.getByRole('button', { name: 'Отправить' }))

		expect(await screen.findByText('RAG-сервис временно недоступен. Попробуй позже.')).toBeInTheDocument()
	})

	it('calls load more from the documents list', async () => {
		const user = userEvent.setup()
		const documents = setupBaseMocks({
			items: [makeDocument()],
			total: 2,
			hasMore: true,
		}).documents

		render(<KnowledgeBaseScreen />)

		await user.click(screen.getByRole('button', { name: 'Загрузить ещё' }))

		expect(documents.loadMore).toHaveBeenCalledTimes(1)
	})
})
