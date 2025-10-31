import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'dist/'
      ]
    },
    env: {
      VITE_API_URL: 'http://localhost:8000',
      VITE_API_TIMEOUT: '30000',
      VITE_API_KEY: 'test-api-key-1234567890abcdefghijklmnop',
      VITE_ENABLE_POLLING: 'true',
      VITE_POLLING_INTERVAL: '5000',
      VITE_ENABLE_VIRTUAL_SCROLL: 'true',
      VITE_VIRTUAL_SCROLL_THRESHOLD: '100',
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
