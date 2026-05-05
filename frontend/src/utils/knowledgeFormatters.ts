import type { DocumentStatus, RAGConfidence } from '../types/api'

const fileSizeFormatter = new Intl.NumberFormat('ru-RU', {
	maximumFractionDigits: 1,
})

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
	day: '2-digit',
	month: 'short',
	hour: '2-digit',
	minute: '2-digit',
})

export function formatFileSize(sizeBytes: number): string {
	if (!Number.isFinite(sizeBytes) || sizeBytes <= 0) {
		return '0 Б'
	}

	const units = ['Б', 'КБ', 'МБ', 'ГБ']
	let size = sizeBytes
	let unitIndex = 0

	while (size >= 1024 && unitIndex < units.length - 1) {
		size /= 1024
		unitIndex += 1
	}

	const roundedSize = size >= 10 || unitIndex === 0 ? Math.round(size) : Math.round(size * 10) / 10
	return `${fileSizeFormatter.format(roundedSize)} ${units[unitIndex]}`
}

export function formatDocumentStatus(status: DocumentStatus): string {
	const labels: Record<DocumentStatus, string> = {
		processing: 'Обработка',
		ready: 'Готов',
		failed: 'Ошибка',
	}

	return labels[status]
}

export function formatDateTime(value: string): string {
	const date = new Date(value)

	if (Number.isNaN(date.getTime())) {
		return 'Дата неизвестна'
	}

	return dateTimeFormatter.format(date).replace(/\.$/, '')
}

export function formatConfidence(confidence: RAGConfidence): string {
	const labels: Record<RAGConfidence, string> = {
		low: 'Низкая уверенность',
		medium: 'Средняя уверенность',
		high: 'Высокая уверенность',
	}

	return labels[confidence]
}

export function sanitizeDisplayedText(text: string | null | undefined): string {
	if (!text) {
		return ''
	}

	return text.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim()
}
