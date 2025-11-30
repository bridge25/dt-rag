/**
 * API Client Configuration
 *
 * Centralized HTTP client for all API calls.
 * Wraps axios with consistent configuration and error handling.
 *
 * @CODE:CLEAN-ARCHITECTURE-DATA
 */

import axios, { type AxiosInstance, type AxiosError, type AxiosRequestConfig } from 'axios';

/**
 * API Error class for consistent error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }

  static fromAxiosError(error: AxiosError<{ message?: string; code?: string; details?: Record<string, unknown> }>): ApiError {
    const response = error.response;
    const data = response?.data;

    return new ApiError(
      data?.message || error.message || 'Unknown API error',
      response?.status || 500,
      data?.code || 'UNKNOWN_ERROR',
      data?.details
    );
  }
}

/**
 * API Client configuration
 */
export interface ApiClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

/**
 * Create a configured API client
 */
export function createApiClient(config: ApiClientConfig): AxiosInstance {
  const client = axios.create({
    baseURL: config.baseUrl,
    timeout: config.timeout || 30000,
    headers: {
      'Content-Type': 'application/json',
      ...(config.apiKey && { 'X-API-Key': config.apiKey }),
    },
  });

  // Request interceptor for logging
  client.interceptors.request.use(
    (requestConfig) => {
      if (process.env.NODE_ENV === 'development') {
        console.debug(`[API] ${requestConfig.method?.toUpperCase()} ${requestConfig.url}`);
      }
      return requestConfig;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<{ message?: string; code?: string; details?: Record<string, unknown> }>) => {
      if (process.env.NODE_ENV === 'development') {
        console.error(`[API Error] ${error.config?.url}:`, error.response?.data || error.message);
      }
      return Promise.reject(ApiError.fromAxiosError(error));
    }
  );

  return client;
}

/**
 * Default API client instance
 */
let defaultClient: AxiosInstance | null = null;

/**
 * Get the default API client (singleton)
 */
export function getApiClient(): AxiosInstance {
  if (!defaultClient) {
    defaultClient = createApiClient({
      baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
      apiKey: process.env.NEXT_PUBLIC_API_KEY,
      timeout: 30000,
    });
  }
  return defaultClient;
}

/**
 * Type-safe API request helper
 */
export async function apiRequest<T>(
  config: AxiosRequestConfig
): Promise<T> {
  const client = getApiClient();
  const response = await client.request<T>(config);
  return response.data;
}
