import axios from "axios"
import { env } from "../env"

export const apiClient = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: env.NEXT_PUBLIC_API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API Error:", error.response.status, error.response.data)
    } else if (error.request) {
      console.error("Network Error:", error.message)
    } else {
      console.error("Request Error:", error.message)
    }
    return Promise.reject(error)
  }
)
