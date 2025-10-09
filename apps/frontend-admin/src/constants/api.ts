/**
 * API Configuration Constants
 * Centralized API settings from environment variables
 */

export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1',
  API_KEY: process.env.NEXT_PUBLIC_API_KEY || '',
} as const

if (typeof window !== 'undefined' && !process.env.NEXT_PUBLIC_API_KEY) {
  console.warn(
    '[API Config] NEXT_PUBLIC_API_KEY is not set. Please configure .env.local file.'
  )
}

export const getApiHeaders = () => ({
  'Content-Type': 'application/json',
  'X-API-Key': API_CONFIG.API_KEY,
})
