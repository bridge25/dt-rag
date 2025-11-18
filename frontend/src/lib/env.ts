import { z } from "zod"

const envSchema = z.object({
  VITE_API_URL: z.string().url().optional().default("http://localhost:8000/api/v1"),
  VITE_API_TIMEOUT: z.string().optional().default("30000").pipe(z.string().regex(/^\d+$/).transform(Number)),
  VITE_API_KEY: z.string().min(32).optional(),
})

const parsedEnv = envSchema.safeParse({
  VITE_API_URL: import.meta.env.VITE_API_URL,
  VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
  VITE_API_KEY: import.meta.env.VITE_API_KEY,
})

if (!parsedEnv.success) {
  console.error("Environment validation failed:", parsedEnv.error.format())
  throw new Error("Invalid environment variables")
}

export const env = parsedEnv.data
