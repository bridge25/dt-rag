import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { API_ENDPOINTS, DEFAULT_HEADERS } from '@/constants/api'
import type { ApiResponse } from '@/types/common'

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: API_ENDPOINTS.BASE_URL,
      headers: DEFAULT_HEADERS,
      timeout: 10000, // 10초 타임아웃
    })

    // 요청 인터셉터
    this.instance.interceptors.request.use(
      (config) => {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
      }
    )

    // 응답 인터셉터
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`[API Response] ${response.status} ${response.config.url}`)
        return response
      },
      (error) => {
        console.error('[API Response Error]', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const response = await this.instance.get<ApiResponse<T>>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.post<ApiResponse<T>>(url, data)
    return response.data
  }

  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    const response = await this.instance.put<ApiResponse<T>>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    const response = await this.instance.delete<ApiResponse<T>>(url)
    return response.data
  }
}

export const apiClient = new ApiClient()