import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  // Debug: Log environment variables during build
  console.log('=== VITE BUILD DEBUG ===')
  console.log('Mode:', mode)
  console.log('VITE_API_URL:', env.VITE_API_URL || 'UNDEFINED')
  console.log('VITE_API_KEY:', env.VITE_API_KEY ? '***' + env.VITE_API_KEY.slice(-4) : 'UNDEFINED')
  console.log('=======================')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  }
})
