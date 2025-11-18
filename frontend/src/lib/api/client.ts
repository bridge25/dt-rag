// @CODE:FRONTEND-INTEGRATION-001:API-CLIENT
import axios from 'axios'
import type { AxiosInstance, AxiosError } from 'axios'
import { env } from '@/lib/config/env'

export class APIError extends Error {
  public status: number
  public title: string
  public detail: string
  public type?: string

  constructor(status: number, title: string, detail: string, type?: string) {
    super(detail)
    this.name = 'APIError'
    this.status = status
    this.title = title
    this.detail = detail
    this.type = type
  }
}

export class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: env.VITE_API_URL,
      timeout: env.VITE_API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': env.VITE_API_KEY,
      },
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          const { status, data } = error.response
          const problemDetails = data as unknown as { title?: string; detail?: string; type?: string }
          throw new APIError(
            status,
            problemDetails.title || 'Request Failed',
            problemDetails.detail || error.message,
            problemDetails.type
          )
        } else if (error.request) {
          throw new APIError(0, 'Network Error', 'Network connection failed')
        } else {
          throw new APIError(0, 'Unknown Error', error.message)
        }
      }
    )
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: unknown): Promise<T> {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }
}

export const apiClient = new APIClient()
