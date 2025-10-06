import { z } from "zod"

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url().optional().default("http://localhost:8000"),
  NEXT_PUBLIC_API_TIMEOUT: z.string().optional().default("30000").pipe(z.string().regex(/^\d+$/).transform(Number)),
})

const parsedEnv = envSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_API_TIMEOUT: process.env.NEXT_PUBLIC_API_TIMEOUT,
})

if (!parsedEnv.success) {
  console.error("Environment validation failed:", parsedEnv.error.format())
  throw new Error("Invalid environment variables")
}

export const env = parsedEnv.data
