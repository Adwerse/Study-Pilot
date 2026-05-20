import { describe, expect, it } from 'vitest'
import { formatConfidence, formatDocumentStatus, formatFileSize, sanitizeDisplayedText } from './knowledgeFormatters'

describe('knowledgeFormatters', () => {
	it('formats file sizes', () => {
		expect(formatFileSize(12_345)).toBe('12 KB')
		expect(formatFileSize(1_048_576)).toBe('1 MB')
		expect(formatFileSize(0)).toBe('0 B')
	})

	it('formats document statuses', () => {
		expect(formatDocumentStatus('processing')).toBe('Processing')
		expect(formatDocumentStatus('ready')).toBe('Ready')
		expect(formatDocumentStatus('failed')).toBe('Error')
	})

	it('formats confidence levels', () => {
		expect(formatConfidence('low')).toBe('Low confidence')
		expect(formatConfidence('medium')).toBe('Medium confidence')
		expect(formatConfidence('high')).toBe('High confidence')
	})

	it('strips unsafe control characters from displayed text', () => {
		expect(sanitizeDisplayedText('  hello\u0000 world\u0007  ')).toBe('hello world')
	})
})
