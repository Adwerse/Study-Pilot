import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
	plugins: [react()],
	server: {
		port: 5173,
		host: true,
		strictPort: true,
		allowedHosts: true,
		proxy: {
			'/api': 'http://127.0.0.1:8000',
		},
	},
	test: {
		globals: true,
		environment: 'jsdom',
		setupFiles: ['./src/test/setup.ts'],
	},
	define: {
		global: 'globalThis',
	},
	build: {
		outDir: 'dist',
		sourcemap: true,
	},
})
