import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
	plugins: [react()],
	server: {
		port: 5173,
		host: true,
		strictPort: true,
		allowedHosts: true,
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
