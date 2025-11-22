/**
 * Environment configuration validation
 *
 * @CODE:FRONTEND-001
 */
import { z } from 'zod'

const envSchema = z.object({
  VITE_API_URL: z.string().url('Invalid API URL format'),
  VITE_API_KEY: z.string().min(1, 'API key is required'),
  VITE_API_TIMEOUT: z.coerce.number().positive('Timeout must be positive').default(10000),
  VITE_ENABLE_POLLING: z.coerce.boolean().default(true),
  VITE_POLLING_INTERVAL: z.coerce.number().positive('Polling interval must be positive').default(5000),
  VITE_ENABLE_VIRTUAL_SCROLL: z.coerce.boolean().default(true),
  VITE_VIRTUAL_SCROLL_THRESHOLD: z.coerce.number().positive('Virtual scroll threshold must be positive').default(100),
})

export type Env = z.infer<typeof envSchema>

function parseEnv(): Env {
  try {
    return envSchema.parse({
      VITE_API_URL: import.meta.env.VITE_API_URL,
      VITE_API_KEY: import.meta.env.VITE_API_KEY,
      VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
      VITE_ENABLE_POLLING: import.meta.env.VITE_ENABLE_POLLING,
      VITE_POLLING_INTERVAL: import.meta.env.VITE_POLLING_INTERVAL,
      VITE_ENABLE_VIRTUAL_SCROLL: import.meta.env.VITE_ENABLE_VIRTUAL_SCROLL,
      VITE_VIRTUAL_SCROLL_THRESHOLD: import.meta.env.VITE_VIRTUAL_SCROLL_THRESHOLD,
    })
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Environment validation failed:', error.format())
      throw new Error(
        `Invalid environment variables:\n${error.issues.map((e) => `  - ${e.path.join('.')}: ${e.message}`).join('\n')}`
      )
    }
    throw error
  }
}

export const env = parseEnv()
