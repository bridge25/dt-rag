// @TEST:FRONTEND-INTEGRATION-001:API-CLIENT
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

vi.mock('@/lib/config/env', () => ({
  env: {
    VITE_API_URL: 'http://localhost:8000',
    VITE_API_KEY: 'test_key',
    VITE_API_TIMEOUT: 10000,
    VITE_ENABLE_POLLING: true,
    VITE_POLLING_INTERVAL: 5000,
    VITE_ENABLE_VIRTUAL_SCROLL: true,
    VITE_VIRTUAL_SCROLL_THRESHOLD: 100,
  },
}))

describe('APIClient', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create = vi.fn().mockReturnValue(mockAxiosInstance as unknown as ReturnType<typeof axios.create>)
  })

  afterEach(() => {
    vi.resetModules()
  })

  describe('initialization', () => {
    it('should create axios instance with correct config', async () => {
      const { APIClient } = await import('../client')
      new APIClient()

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'http://localhost:8000',
          timeout: 10000,
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('should add Authorization header when API key is provided', async () => {
      const { APIClient } = await import('../client')
      new APIClient()

      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test_key',
          }),
        })
      )
    })
  })

  describe('HTTP methods', () => {
    it('should make GET requests', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { success: true } })

      const { APIClient } = await import('../client')
      const client = new APIClient()
      const result = await client.get('/test')

      expect(result).toEqual({ success: true })
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', { params: undefined })
    })

    it('should make POST requests with data', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { created: true } })

      const { APIClient } = await import('../client')
      const client = new APIClient()
      const result = await client.post('/test', { name: 'test' })

      expect(result).toEqual({ created: true })
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/test', { name: 'test' })
    })

    it('should make PATCH requests with data', async () => {
      mockAxiosInstance.patch.mockResolvedValue({ data: { updated: true } })

      const { APIClient } = await import('../client')
      const client = new APIClient()
      const result = await client.patch('/test/1', { name: 'updated' })

      expect(result).toEqual({ updated: true })
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/test/1', { name: 'updated' })
    })

    it('should make DELETE requests', async () => {
      mockAxiosInstance.delete.mockResolvedValue({ data: { deleted: true } })

      const { APIClient } = await import('../client')
      const client = new APIClient()
      const result = await client.delete('/test/1')

      expect(result).toEqual({ deleted: true })
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test/1')
    })
  })

  describe('APIError class', () => {
    it('should create APIError with all properties', async () => {
      const { APIError } = await import('../client')
      const error = new APIError(404, 'Not Found', 'Resource not found', 'about:blank')

      expect(error.status).toBe(404)
      expect(error.title).toBe('Not Found')
      expect(error.detail).toBe('Resource not found')
      expect(error.type).toBe('about:blank')
      expect(error.message).toBe('Resource not found')
      expect(error.name).toBe('APIError')
    })

    it('should create APIError without optional type', async () => {
      const { APIError } = await import('../client')
      const error = new APIError(500, 'Internal Server Error', 'Something went wrong')

      expect(error.status).toBe(500)
      expect(error.type).toBeUndefined()
    })
  })
})
