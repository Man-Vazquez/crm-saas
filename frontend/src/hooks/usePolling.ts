import { useEffect, useRef } from 'react'

/**
 * Runs `callback` on a fixed interval while `enabled` is true and the tab is
 * visible.  Pauses automatically when the document goes into the background
 * and resumes when it becomes visible again.  Cleans up on unmount.
 */
export function usePolling(
  callback: () => void,
  intervalMs: number,
  enabled: boolean,
): void {
  // Keep a stable ref so we never need to restart the interval when the
  // callback identity changes (e.g. because it closes over fresh state).
  const callbackRef = useRef(callback)
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled) return

    const tick = () => {
      if (document.visibilityState === 'visible') {
        callbackRef.current()
      }
    }

    const id = setInterval(tick, intervalMs)

    // Also fire when the tab comes back into view mid-interval so the user
    // doesn't have to wait up to `intervalMs` for a refresh after switching
    // back to the tab.
    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        callbackRef.current()
      }
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      clearInterval(id)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [intervalMs, enabled])
}
