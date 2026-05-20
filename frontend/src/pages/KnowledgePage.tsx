import { ChangeEvent, CSSProperties, KeyboardEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Badge, Body, Button, Caption, Card, Skeleton, Subtitle, Title } from '../components/ui'
import { useAskQuestion, useDeleteDocument, useDocuments, useUploadDocument } from '../hooks'
import type { ApiError, DocumentStatus, KnowledgeDocument, RAGConfidence, RAGSource } from '../types/api'
import {
	formatConfidence,
	formatDateTime,
	formatDocumentStatus,
	formatFileSize,
	sanitizeDisplayedText,
} from '../utils/knowledgeFormatters'

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
const ACCEPTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md']
const POLLING_INTERVAL_MS = 8000

type KnowledgeTab = 'materials' | 'chat'
type StatusFilter = DocumentStatus | 'all'
type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'info'

type ChatMessage = {
	id: string
	role: 'user' | 'assistant'
	content: string
	sources?: RAGSource[]
	confidence?: RAGConfidence
}

const inputStyle: CSSProperties = {
	width: '100%',
	minHeight: '44px',
	padding: '0 var(--space-3)',
	borderRadius: 'var(--radius-md)',
	border: '1px solid rgba(0, 0, 0, 0.10)',
	background: 'var(--tg-bg)',
	color: 'var(--tg-text)',
	fontSize: 'var(--text-base)',
	outline: 'none',
}

const panelErrorStyle: CSSProperties = {
	border: '1px solid var(--tg-destructive)',
	borderRadius: 'var(--radius-sm)',
	padding: '10px 12px',
	color: 'var(--tg-destructive)',
	background: 'rgba(229, 62, 62, 0.08)',
}

function isApiErrorLike(error: unknown): error is ApiError {
	if (typeof error !== 'object' || error === null) {
		return false
	}

	const maybeError = error as Partial<ApiError>
	return typeof maybeError.detail === 'string' && typeof maybeError.status === 'number'
}

function humanizeApiError(error: unknown, fallback: string): string {
	if (!isApiErrorLike(error)) {
		return fallback
	}

	const detail = error.detail.toLowerCase()

	if (error.status === 401) {
		return 'Open the Mini App through Telegram and sign in.'
	}

	if (error.status === 413) {
		return 'The file is too large. Maximum size is 10 MB.'
	}

	if (error.status === 415 || detail.includes('unsupported')) {
		return 'Only PDF, TXT, and MD files are supported.'
	}

	if (error.status === 422) {
		return 'Check the file or question text and try again.'
	}

	if (detail.includes('database unavailable')) {
		return 'The database is temporarily unavailable. Check that PostgreSQL is running.'
	}

	if (error.status === 503) {
		if (detail.includes('rag')) {
			return 'The RAG service is temporarily unavailable. Try again later.'
		}

		return 'The service is temporarily unavailable. Try again in a minute.'
	}

	if (detail.includes('network')) {
		return 'Check your connection and try again.'
	}

	return fallback
}

function hasSupportedExtension(file: File): boolean {
	const lowerName = file.name.toLowerCase()
	return ACCEPTED_FILE_EXTENSIONS.some((extension) => lowerName.endsWith(extension))
}

function getStatusBadgeTone(status: DocumentStatus): BadgeTone {
	const tones: Record<DocumentStatus, BadgeTone> = {
		processing: 'warning',
		ready: 'success',
		failed: 'danger',
	}

	return tones[status]
}

function getConfidenceBadgeTone(confidence: RAGConfidence): BadgeTone {
	const tones: Record<RAGConfidence, BadgeTone> = {
		low: 'warning',
		medium: 'info',
		high: 'success',
	}

	return tones[confidence]
}

function createMessageId(role: ChatMessage['role']): string {
	return `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function UploadBlock({
	onUploaded,
}: {
	onUploaded: () => void
}) {
	const [selectedFile, setSelectedFile] = useState<File | null>(null)
	const [title, setTitle] = useState('')
	const [fileInputKey, setFileInputKey] = useState(0)
	const [localError, setLocalError] = useState<string | null>(null)
	const [successMessage, setSuccessMessage] = useState<string | null>(null)
	const uploadState = useUploadDocument((document) => {
		setSuccessMessage(
			document.status === 'processing'
				? 'The file is processing and will appear in chat soon'
				: document.status === 'ready'
					? 'The material is ready for chat'
					: 'The file uploaded, but processing failed',
		)
		onUploaded()
	})

	const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
		const file = event.target.files?.[0] ?? null
		uploadState.reset()
		setSuccessMessage(null)
		setLocalError(null)

		if (!file) {
			setSelectedFile(null)
			return
		}

		if (!hasSupportedExtension(file)) {
			setSelectedFile(null)
			setLocalError('Only PDF, TXT, and MD files are supported.')
			event.target.value = ''
			return
		}

		if (file.size > MAX_FILE_SIZE_BYTES) {
			setSelectedFile(null)
			setLocalError('The file is too large. Maximum size is 10 MB.')
			event.target.value = ''
			return
		}

		setSelectedFile(file)
		if (!title.trim()) {
			setTitle(file.name.replace(/\.[^.]+$/, ''))
		}
	}

	const handleUpload = () => {
		if (!selectedFile) {
			setLocalError('Choose a file to upload.')
			return
		}

		setLocalError(null)
		setSuccessMessage(null)

		void uploadState
			.upload(selectedFile, {
				title: title.trim() || undefined,
				source_type: 'upload',
			})
			.then(() => {
				setSelectedFile(null)
				setTitle('')
				setFileInputKey((previous) => previous + 1)
			})
			.catch((error) => {
				setLocalError(humanizeApiError(error, 'Unable to upload file'))
			})
	}

	const uploadError = localError ?? (uploadState.error ? humanizeApiError(uploadState.error, 'Unable to upload file') : null)

	return (
		<Card>
			<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
				<div style={{ display: 'grid', gap: '4px' }}>
					<Subtitle>Upload material</Subtitle>
					<Caption>PDF, TXT, or MD up to 10 MB</Caption>
				</div>

				<input
					key={fileInputKey}
					aria-label="Material file"
					type="file"
					accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown,text/x-markdown"
					onChange={handleFileChange}
					style={{
						...inputStyle,
						paddingTop: '10px',
						background: 'var(--tg-secondary-bg)',
					}}
				/>

				<input
					aria-label="Material title"
					value={title}
					onChange={(event) => setTitle(event.target.value)}
					placeholder="Title, if needed"
					style={inputStyle}
				/>

				<Button
					variant="primary"
					size="md"
					fullWidth
					loading={uploadState.uploading}
					disabled={!selectedFile}
					onClick={handleUpload}
				>
					Upload
				</Button>

				{uploadState.uploading && uploadState.progress !== null ? (
					<div style={{ display: 'grid', gap: '4px' }}>
						<progress aria-label="Upload progress" value={uploadState.progress} max={100} style={{ width: '100%' }} />
						<Caption>{uploadState.progress}%</Caption>
					</div>
				) : null}

				{selectedFile ? (
					<Caption>
						{selectedFile.name} · {formatFileSize(selectedFile.size)}
					</Caption>
				) : null}

				{successMessage ? <Caption style={{ color: 'var(--tg-success)' }}>{successMessage}</Caption> : null}
				{uploadError ? <Caption style={{ color: 'var(--tg-destructive)' }}>{uploadError}</Caption> : null}
			</div>
		</Card>
	)
}

function SegmentTabs({
	activeTab,
	onChange,
}: {
	activeTab: KnowledgeTab
	onChange: (tab: KnowledgeTab) => void
}) {
	const tabs: Array<{ id: KnowledgeTab; label: string }> = [
		{ id: 'materials', label: 'Materials' },
		{ id: 'chat', label: 'Chat' },
	]

	return (
		<div
			role="tablist"
			aria-label="Knowledge base sections"
			style={{
				display: 'grid',
				gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
				gap: '4px',
				padding: '4px',
				borderRadius: 'var(--radius-md)',
				background: 'var(--tg-secondary-bg)',
			}}
		>
			{tabs.map((tab) => {
				const active = activeTab === tab.id

				return (
					<button
						key={tab.id}
						type="button"
						role="tab"
						aria-selected={active}
						onClick={() => onChange(tab.id)}
						style={{
							minHeight: '40px',
							border: 'none',
							borderRadius: 'var(--radius-sm)',
							background: active ? 'var(--tg-bg)' : 'transparent',
							color: active ? 'var(--tg-text)' : 'var(--tg-hint)',
							fontWeight: 600,
							fontSize: 'var(--text-base)',
							boxShadow: active ? 'var(--shadow-sm)' : 'none',
						}}
					>
						{tab.label}
					</button>
				)
			})}
		</div>
	)
}

function DocumentsFilters({
	query,
	status,
	onQueryChange,
	onStatusChange,
}: {
	query: string
	status: StatusFilter
	onQueryChange: (value: string) => void
	onStatusChange: (value: StatusFilter) => void
}) {
	return (
		<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
			<input
				aria-label="Search materials"
				value={query}
				onChange={(event) => onQueryChange(event.target.value)}
				placeholder="Search materials"
				style={inputStyle}
			/>
			<select
				aria-label="Status filter"
				value={status}
				onChange={(event) => onStatusChange(event.target.value as StatusFilter)}
				style={{
					...inputStyle,
					appearance: 'none',
				}}
			>
				<option value="all">All statuses</option>
				<option value="ready">Ready</option>
				<option value="processing">Processing</option>
				<option value="failed">Error</option>
			</select>
		</div>
	)
}

function DocumentCard({
	document,
	selected,
	deleting,
	onToggleSelected,
	onDelete,
}: {
	document: KnowledgeDocument
	selected: boolean
	deleting: boolean
	onToggleSelected: (documentId: string) => void
	onDelete: (document: KnowledgeDocument) => void
}) {
	const canSelect = document.status === 'ready'

	return (
		<Card padding="sm">
			<div style={{ display: 'grid', gap: 'var(--space-2)' }}>
				<div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
					<div style={{ minWidth: 0, display: 'grid', gap: '2px' }}>
						<strong
							style={{
								color: 'var(--tg-text)',
								fontSize: 'var(--text-base)',
								overflowWrap: 'anywhere',
							}}
						>
							{sanitizeDisplayedText(document.title) || document.filename}
						</strong>
						<Caption style={{ overflowWrap: 'anywhere' }}>{document.filename}</Caption>
					</div>
					<Badge variant={getStatusBadgeTone(document.status)}>{formatDocumentStatus(document.status)}</Badge>
				</div>

				<div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 10px' }}>
					<Caption>{document.chunks_count} chunks</Caption>
					<Caption>{formatFileSize(document.size_bytes)}</Caption>
					<Caption>{formatDateTime(document.created_at)}</Caption>
				</div>

				{document.status === 'failed' && document.error_message ? (
					<Caption style={{ color: 'var(--tg-destructive)', overflowWrap: 'anywhere' }}>
						{sanitizeDisplayedText(document.error_message)}
					</Caption>
				) : null}

				<div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
					<label
						style={{
							minHeight: '36px',
							display: 'inline-flex',
							alignItems: 'center',
							gap: '8px',
							color: canSelect ? 'var(--tg-text)' : 'var(--tg-hint)',
							fontSize: 'var(--text-sm)',
						}}
					>
						<input
							type="checkbox"
							checked={selected}
							disabled={!canSelect}
							onChange={() => onToggleSelected(document.id)}
							style={{ width: '18px', height: '18px' }}
						/>
						Search
					</label>

					<Button variant="ghost" size="sm" loading={deleting} onClick={() => onDelete(document)}>
						Delete
					</Button>
				</div>
			</div>
		</Card>
	)
}

function DocumentsList({
	documents,
	total,
	loading,
	loadingMore,
	error,
	hasMore,
	onRetry,
	onLoadMore,
	selectedDocumentIds,
	onToggleSelected,
	onDelete,
	isDeleting,
	deleteError,
}: {
	documents: KnowledgeDocument[]
	total: number
	loading: boolean
	loadingMore: boolean
	error: ApiError | null
	hasMore: boolean
	onRetry: () => void
	onLoadMore: () => void
	selectedDocumentIds: string[]
	onToggleSelected: (documentId: string) => void
	onDelete: (document: KnowledgeDocument) => void
	isDeleting: (documentId: string) => boolean
	deleteError: ApiError | null
}) {
	if (loading) {
		return (
			<div aria-label="Loading materials" style={{ display: 'grid', gap: 'var(--space-3)' }}>
				<Skeleton height={86} borderRadius="12px" />
				<Skeleton height={86} borderRadius="12px" />
				<Skeleton height={86} borderRadius="12px" />
			</div>
		)
	}

	if (error) {
		return (
			<Card>
				<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
					<Body style={{ color: 'var(--tg-destructive)' }}>
						{humanizeApiError(error, 'Unable to load materials list')}
					</Body>
					<Button variant="secondary" size="md" onClick={onRetry}>
						Retry
					</Button>
				</div>
			</Card>
		)
	}

	if (documents.length === 0) {
		return (
			<Card>
				<div style={{ display: 'grid', gap: '4px', textAlign: 'center', padding: 'var(--space-3) 0' }}>
					<Subtitle>No materials yet</Subtitle>
					<Caption>Upload a PDF, TXT, or MD file so StudyPilot can answer from it.</Caption>
				</div>
			</Card>
		)
	}

	return (
		<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
			<div style={{ display: 'flex', justifyContent: 'space-between', gap: 'var(--space-2)', alignItems: 'center' }}>
				<Caption>
					{documents.length} of {total}
				</Caption>
				<Caption>Search selected materials only</Caption>
			</div>

			{deleteError ? (
				<Caption style={{ ...panelErrorStyle, display: 'block' }}>
					{humanizeApiError(deleteError, 'Unable to delete material')}
				</Caption>
			) : null}

			{documents.map((document) => (
				<DocumentCard
					key={document.id}
					document={document}
					selected={selectedDocumentIds.includes(document.id)}
					deleting={isDeleting(document.id)}
					onToggleSelected={onToggleSelected}
					onDelete={onDelete}
				/>
			))}

			{hasMore ? (
				<Button variant="secondary" size="md" fullWidth loading={loadingMore} onClick={onLoadMore}>
					Load more
				</Button>
			) : null}
		</div>
	)
}

function MessageBubble({ message }: { message: ChatMessage }) {
	const isUser = message.role === 'user'

	return (
		<div
			style={{
				display: 'grid',
				justifyItems: isUser ? 'end' : 'start',
			}}
		>
			<div
				style={{
					maxWidth: '92%',
					padding: '10px 12px',
					borderRadius: 'var(--radius-md)',
					background: isUser ? 'var(--tg-button)' : 'var(--tg-secondary-bg)',
					color: isUser ? 'var(--tg-button-text)' : 'var(--tg-text)',
					whiteSpace: 'pre-wrap',
					overflowWrap: 'anywhere',
				}}
			>
				{sanitizeDisplayedText(message.content)}
			</div>

			{message.role === 'assistant' ? (
				<div style={{ width: '100%', marginTop: 'var(--space-2)', display: 'grid', gap: 'var(--space-2)' }}>
					{message.confidence ? (
						<Badge variant={getConfidenceBadgeTone(message.confidence)}>{formatConfidence(message.confidence)}</Badge>
					) : null}
					<SourcesList sources={message.sources ?? []} />
				</div>
			) : null}
		</div>
	)
}

function SourcesList({ sources }: { sources: RAGSource[] }) {
	if (sources.length === 0) {
		return <Caption>Answer without sources: not enough data.</Caption>
	}

	return (
		<details open style={{ display: 'grid', gap: 'var(--space-2)' }}>
			<summary
				style={{
					minHeight: '32px',
					color: 'var(--tg-text)',
					fontWeight: 600,
					fontSize: 'var(--text-sm)',
					cursor: 'pointer',
				}}
			>
				Sources
			</summary>
			<div style={{ display: 'grid', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
				{sources.map((source, index) => (
					<div
						key={`${source.document_id}-${source.chunk_id}`}
						style={{
							padding: '10px',
							borderRadius: 'var(--radius-sm)',
							background: 'var(--tg-secondary-bg)',
							display: 'grid',
							gap: '4px',
						}}
					>
						<Caption style={{ color: 'var(--tg-text)', fontWeight: 600 }}>
							[{index + 1}] {sanitizeDisplayedText(source.document_title) || source.filename}
							{source.page_number ? ` · p. ${source.page_number}` : ''}
						</Caption>
						<Caption
							style={{
								display: '-webkit-box',
								WebkitLineClamp: 3,
								WebkitBoxOrient: 'vertical',
								overflow: 'hidden',
								overflowWrap: 'anywhere',
							}}
						>
							"{sanitizeDisplayedText(source.snippet)}"
						</Caption>
					</div>
				))}
			</div>
		</details>
	)
}

function RagChat({
	readyDocumentsCount,
	processingDocumentsCount,
	selectedDocumentIds,
}: {
	readyDocumentsCount: number
	processingDocumentsCount: number
	selectedDocumentIds: string[]
}) {
	const [messages, setMessages] = useState<ChatMessage[]>([])
	const [question, setQuestion] = useState('')
	const [localError, setLocalError] = useState<string | null>(null)
	const askState = useAskQuestion()
	const hasReadyDocuments = readyDocumentsCount > 0

	const handleSend = useCallback(() => {
		const normalizedQuestion = question.trim()

		if (!normalizedQuestion) {
			setLocalError('Write a question about your materials.')
			return
		}

		if (!hasReadyDocuments) {
			setLocalError('Upload a material first, then you can ask questions.')
			return
		}

		const userMessage: ChatMessage = {
			id: createMessageId('user'),
			role: 'user',
			content: normalizedQuestion,
		}

		setMessages((previous) => [...previous, userMessage])
		setQuestion('')
		setLocalError(null)
		askState.clearError()

		void askState
			.ask(normalizedQuestion, {
				document_ids: selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
			})
			.then((response) => {
				setMessages((previous) => [
					...previous,
					{
						id: createMessageId('assistant'),
						role: 'assistant',
						content: response.answer,
						sources: response.sources,
						confidence: response.confidence,
					},
				])
			})
			.catch((error) => {
				setLocalError(humanizeApiError(error, 'Unable to get an answer'))
			})
	}, [askState, hasReadyDocuments, question, selectedDocumentIds])

	const handleQuestionKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault()
			handleSend()
		}
	}

	const chatError = localError ?? (askState.error ? humanizeApiError(askState.error, 'Unable to get an answer') : null)

	return (
		<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
			{!hasReadyDocuments ? (
				<Card>
					<Caption>Upload a material first, then you can ask questions.</Caption>
				</Card>
			) : null}

			{processingDocumentsCount > 0 ? (
				<Card padding="sm">
					<Caption>Some materials are still processing.</Caption>
				</Card>
			) : null}

			{selectedDocumentIds.length > 0 ? (
				<Caption>Search is limited to selected materials: {selectedDocumentIds.length}</Caption>
			) : (
				<Caption>If nothing is selected, search uses all ready materials.</Caption>
			)}

			<div style={{ display: 'grid', gap: 'var(--space-3)' }}>
				{messages.length === 0 ? (
					<Card>
						<Caption>Ask a question about uploaded materials. The answer will appear with sources.</Caption>
					</Card>
				) : (
					messages.map((message) => <MessageBubble key={message.id} message={message} />)
				)}

				{askState.loading ? (
					<div style={{ display: 'grid', justifyItems: 'start' }}>
						<div
							style={{
								padding: '10px 12px',
								borderRadius: 'var(--radius-md)',
								background: 'var(--tg-secondary-bg)',
							}}
						>
							<Caption>Searching materials...</Caption>
						</div>
					</div>
				) : null}
			</div>

			<div
				style={{
					position: 'sticky',
					bottom: '72px',
					display: 'grid',
					gap: 'var(--space-2)',
					paddingTop: 'var(--space-2)',
					background: 'var(--tg-bg)',
				}}
			>
				<textarea
					aria-label="Question"
					value={question}
					onChange={(event) => setQuestion(event.target.value)}
					onKeyDown={handleQuestionKeyDown}
					placeholder="Ask about your materials"
					disabled={!hasReadyDocuments || askState.loading}
					rows={3}
					style={{
						...inputStyle,
						minHeight: '88px',
						paddingTop: '10px',
						resize: 'vertical',
						opacity: !hasReadyDocuments ? 0.6 : 1,
					}}
				/>
				<Button
					variant="primary"
					size="md"
					fullWidth
					loading={askState.loading}
					disabled={!hasReadyDocuments || !question.trim()}
					onClick={handleSend}
				>
					Send
				</Button>
				{chatError ? <Caption style={{ color: 'var(--tg-destructive)' }}>{chatError}</Caption> : null}
			</div>
		</div>
	)
}

export function KnowledgeBaseScreen() {
	const [activeTab, setActiveTab] = useState<KnowledgeTab>('materials')
	const [searchQuery, setSearchQuery] = useState('')
	const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
	const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([])
	const documentParams = useMemo(
		() => ({
			limit: 10,
			status: statusFilter === 'all' ? undefined : statusFilter,
			q: searchQuery,
		}),
		[searchQuery, statusFilter],
	)
	const documentsState = useDocuments(documentParams)
	const readyDocuments = useMemo(
		() => documentsState.items.filter((document) => document.status === 'ready'),
		[documentsState.items],
	)
	const readyDocumentIds = useMemo(() => new Set(readyDocuments.map((document) => document.id)), [readyDocuments])
	const processingDocumentsCount = documentsState.items.filter((document) => document.status === 'processing').length
	const hasProcessingDocuments = processingDocumentsCount > 0
	const refetchDocuments = documentsState.refetch

	const deleteState = useDeleteDocument((documentId) => {
		setSelectedDocumentIds((previous) => previous.filter((id) => id !== documentId))
		refetchDocuments()
	})

	useEffect(() => {
		setSelectedDocumentIds((previous) => previous.filter((documentId) => readyDocumentIds.has(documentId)))
	}, [readyDocumentIds])

	useEffect(() => {
		if (!hasProcessingDocuments) {
			return undefined
		}

		const intervalId = window.setInterval(() => {
			refetchDocuments()
		}, POLLING_INTERVAL_MS)

		return () => {
			window.clearInterval(intervalId)
		}
	}, [hasProcessingDocuments, refetchDocuments])

	const handleUploaded = useCallback(() => {
		refetchDocuments()
		setActiveTab('materials')
	}, [refetchDocuments])

	const handleToggleSelected = (documentId: string) => {
		if (!readyDocumentIds.has(documentId)) {
			return
		}

		setSelectedDocumentIds((previous) =>
			previous.includes(documentId) ? previous.filter((id) => id !== documentId) : [...previous, documentId],
		)
	}

	const handleDelete = (document: KnowledgeDocument) => {
		const confirmed = window.confirm('Delete this material? Answers from it will no longer be available.')

		if (!confirmed) {
			return
		}

		void deleteState.deleteDocument(document.id).catch(() => undefined)
	}

	return (
		<div style={{ padding: 'var(--space-4)', display: 'grid', gap: 'var(--space-4)' }}>
			<header style={{ display: 'grid', gap: '4px' }}>
				<Title>Knowledge Base</Title>
				<Caption>Materials for the StudyPilot RAG assistant</Caption>
			</header>

			<UploadBlock onUploaded={handleUploaded} />

			<SegmentTabs activeTab={activeTab} onChange={setActiveTab} />

			{activeTab === 'materials' ? (
				<section style={{ display: 'grid', gap: 'var(--space-3)' }}>
					<DocumentsFilters
						query={searchQuery}
						status={statusFilter}
						onQueryChange={setSearchQuery}
						onStatusChange={setStatusFilter}
					/>
					<DocumentsList
						documents={documentsState.items}
						total={documentsState.total}
						loading={documentsState.loading}
						loadingMore={documentsState.loadingMore}
						error={documentsState.error}
						hasMore={documentsState.hasMore}
						onRetry={documentsState.refetch}
						onLoadMore={documentsState.loadMore}
						selectedDocumentIds={selectedDocumentIds}
						onToggleSelected={handleToggleSelected}
						onDelete={handleDelete}
						isDeleting={deleteState.isDeleting}
						deleteError={deleteState.error}
					/>
				</section>
			) : (
				<RagChat
					readyDocumentsCount={readyDocuments.length}
					processingDocumentsCount={processingDocumentsCount}
					selectedDocumentIds={selectedDocumentIds}
				/>
			)}
		</div>
	)
}

export function KnowledgePage() {
	return <KnowledgeBaseScreen />
}
