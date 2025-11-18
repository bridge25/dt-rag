// @TEST:FRONTEND-INTEGRATION-001:ENV-CONFIG
import { describe, it, expect } from 'vitest'
import { z } from 'zod'

describe('env configuration', () => {
  const envSchema = z.object({
    VITE_API_URL: z.string().url('Invalid API URL format'),
    VITE_API_KEY: z.string().min(1, 'API key is required'),
    VITE_API_TIMEOUT: z.coerce.number().positive('Timeout must be positive').default(10000),
    VITE_ENABLE_POLLING: z.coerce.boolean().default(true),
    VITE_POLLING_INTERVAL: z.coerce.number().positive('Polling interval must be positive').default(5000),
    VITE_ENABLE_VIRTUAL_SCROLL: z.coerce.boolean().default(true),
    VITE_VIRTUAL_SCROLL_THRESHOLD: z.coerce.number().positive('Virtual scroll threshold must be positive').default(100),
  })

  describe('environment variable validation', () => {
    it('should successfully parse valid environment variables', () => {
      const result = envSchema.parse({
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_KEY: 'test_api_key_123',
        VITE_API_TIMEOUT: '10000',
        VITE_ENABLE_POLLING: 'true',
        VITE_POLLING_INTERVAL: '5000',
        VITE_ENABLE_VIRTUAL_SCROLL: 'true',
        VITE_VIRTUAL_SCROLL_THRESHOLD: '100',
      })

      expect(result.VITE_API_URL).toBe('http://localhost:8000')
      expect(result.VITE_API_KEY).toBe('test_api_key_123')
      expect(result.VITE_API_TIMEOUT).toBe(10000)
      expect(result.VITE_ENABLE_POLLING).toBe(true)
      expect(result.VITE_POLLING_INTERVAL).toBe(5000)
      expect(result.VITE_ENABLE_VIRTUAL_SCROLL).toBe(true)
      expect(result.VITE_VIRTUAL_SCROLL_THRESHOLD).toBe(100)
    })

    it('should apply default values when optional variables are missing', () => {
      const result = envSchema.parse({
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_KEY: 'test_key',
      })

      expect(result.VITE_API_TIMEOUT).toBe(10000)
      expect(result.VITE_ENABLE_POLLING).toBe(true)
      expect(result.VITE_POLLING_INTERVAL).toBe(5000)
      expect(result.VITE_ENABLE_VIRTUAL_SCROLL).toBe(true)
      expect(result.VITE_VIRTUAL_SCROLL_THRESHOLD).toBe(100)
    })

    it('should reject invalid URL format', () => {
      expect(() => {
        envSchema.parse({
          VITE_API_URL: 'not-a-valid-url',
          VITE_API_KEY: 'test_key',
        })
      }).toThrow()
    })

    it('should reject when required VITE_API_URL is missing', () => {
      expect(() => {
        envSchema.parse({
          VITE_API_KEY: 'test_key',
        })
      }).toThrow()
    })

    it('should reject when required VITE_API_KEY is missing', () => {
      expect(() => {
        envSchema.parse({
          VITE_API_URL: 'http://localhost:8000',
        })
      }).toThrow()
    })

    it('should reject negative timeout values', () => {
      expect(() => {
        envSchema.parse({
          VITE_API_URL: 'http://localhost:8000',
          VITE_API_KEY: 'test_key',
          VITE_API_TIMEOUT: '-1000',
        })
      }).toThrow()
    })

    it('should reject non-numeric timeout values', () => {
      expect(() => {
        envSchema.parse({
          VITE_API_URL: 'http://localhost:8000',
          VITE_API_KEY: 'test_key',
          VITE_API_TIMEOUT: 'not-a-number',
        })
      }).toThrow()
    })

    it('should correctly parse boolean values', () => {
      const resultTrue = envSchema.parse({
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_KEY: 'test_key',
        VITE_ENABLE_POLLING: true,
        VITE_ENABLE_VIRTUAL_SCROLL: 1,
      })

      expect(resultTrue.VITE_ENABLE_POLLING).toBe(true)
      expect(resultTrue.VITE_ENABLE_VIRTUAL_SCROLL).toBe(true)

      const resultFalse = envSchema.parse({
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_KEY: 'test_key',
        VITE_ENABLE_POLLING: false,
        VITE_ENABLE_VIRTUAL_SCROLL: 0,
      })

      expect(resultFalse.VITE_ENABLE_POLLING).toBe(false)
      expect(resultFalse.VITE_ENABLE_VIRTUAL_SCROLL).toBe(false)
    })
  })

  describe('type safety', () => {
    it('should validate types correctly', () => {
      const result = envSchema.parse({
        VITE_API_URL: 'http://localhost:8000',
        VITE_API_KEY: 'test_key',
      })

      expect(typeof result.VITE_API_URL).toBe('string')
      expect(typeof result.VITE_API_KEY).toBe('string')
      expect(typeof result.VITE_API_TIMEOUT).toBe('number')
      expect(typeof result.VITE_ENABLE_POLLING).toBe('boolean')
      expect(typeof result.VITE_POLLING_INTERVAL).toBe('number')
      expect(typeof result.VITE_ENABLE_VIRTUAL_SCROLL).toBe('boolean')
      expect(typeof result.VITE_VIRTUAL_SCROLL_THRESHOLD).toBe('number')
    })
  })
})
