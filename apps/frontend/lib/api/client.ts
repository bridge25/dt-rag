/**
 * API client configuration
 *
 * @CODE:FRONTEND-001
 */

import axios from "axios"
import { toast } from "sonner"
import { env } from "../env"

export const apiClient = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: env.NEXT_PUBLIC_API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    ...(env.NEXT_PUBLIC_API_KEY && { "X-API-Key": env.NEXT_PUBLIC_API_KEY }),
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || "An unexpected error occurred"

    if (error.response) {
      // Server responded with error code
      console.error("API Error:", error.response.status, error.response.data)
      toast.error(`Error ${error.response.status}: ${message}`)
    } else if (error.request) {
      // Request made but no response
      console.error("Network Error:", error.message)
      toast.error("Network Error: Please check your connection")
    } else {
      // Request setup error
      console.error("Request Error:", error.message)
      toast.error(`Request Error: ${message}`)
    }
    return Promise.reject(error)
  }
)
