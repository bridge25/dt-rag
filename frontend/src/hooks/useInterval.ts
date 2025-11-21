/**
 * Hook for managing intervals with cleanup and callback updates
 *
 * @CODE:FRONTEND-001
 */
import { useEffect, useRef } from 'react'

export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<(() => void) | undefined>(undefined)

  useEffect(() => {
    savedCallback.current = callback
  }, [callback])

  useEffect(() => {
    if (delay === null) {
      return
    }

    const tick = () => {
      savedCallback.current?.()
    }

    const id = setInterval(tick, delay)
    return () => clearInterval(id)
  }, [delay])
}
