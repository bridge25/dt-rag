interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class ApiCache {
  private cache: Map<string, CacheEntry<any>> = new Map()

  set<T>(key: string, data: T, ttlMs: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttlMs,
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)

    if (!entry) {
      return null
    }

    const isExpired = Date.now() - entry.timestamp > entry.ttl

    if (isExpired) {
      this.cache.delete(key)
      return null
    }

    return entry.data as T
  }

  invalidate(key: string): void {
    this.cache.delete(key)
  }

  invalidateByPrefix(prefix: string): void {
    const keysToDelete: string[] = []

    this.cache.forEach((_, key) => {
      if (key.startsWith(prefix)) {
        keysToDelete.push(key)
      }
    })

    keysToDelete.forEach((key) => {
      this.cache.delete(key)
    })
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }
}

export const apiCache = new ApiCache()

export const CACHE_TTL = {
  TAXONOMY_VERSIONS: 5 * 60 * 1000,
  TAXONOMY_TREE: 10 * 60 * 1000,
  TAXONOMY_STATISTICS: 5 * 60 * 1000,
  TAXONOMY_SEARCH: 2 * 60 * 1000,
  TAXONOMY_COMPARISON: 10 * 60 * 1000,
  HITL_TASKS: 30 * 1000,
  API_STATUS: 60 * 1000,
} as const
