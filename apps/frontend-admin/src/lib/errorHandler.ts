export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message
  }

  if (error instanceof Error) {
    if (error.name === 'AbortError') {
      return 'Request was cancelled'
    }
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  return 'An unexpected error occurred'
}

export function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError'
}

export async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API request failed: ${response.statusText}`
    let details: unknown

    try {
      const errorData = await response.json()
      errorMessage = errorData.message || errorData.detail || errorMessage
      details = errorData
    } catch {
      // Response body is not JSON
    }

    throw new ApiError(errorMessage, response.status, details)
  }

  return response.json()
}
