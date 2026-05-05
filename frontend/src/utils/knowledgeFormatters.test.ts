import { describe, expect, it } from 'vitest'
import { formatConfidence, formatDocumentStatus, formatFileSize, sanitizeDisplayedText } from './knowledgeFormatters'

describe('knowledgeFormatters', () => {
	it('formats file sizes', () => {
		expect(formatFileSize(12_345)).toBe('12 КБ')
		expect(formatFileSize(1_048_576)).toBe('1 МБ')
		expect(formatFileSize(0)).toBe('0 Б')
	})

	it('formats document statuses', () => {
		expect(formatDocumentStatus('processing')).toBe('Обработка')
		expect(formatDocumentStatus('ready')).toBe('Готов')
		expect(formatDocumentStatus('failed')).toBe('Ошибка')
	})

	it('formats confidence levels', () => {
		expect(formatConfidence('low')).toBe('Низкая уверенность')
		expect(formatConfidence('medium')).toBe('Средняя уверенность')
		expect(formatConfidence('high')).toBe('Высокая уверенность')
	})

	it('strips unsafe control characters from displayed text', () => {
		expect(sanitizeDisplayedText('  hello\u0000 world\u0007  ')).toBe('hello world')
	})
})
