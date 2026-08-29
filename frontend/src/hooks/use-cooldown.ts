"use client"

import { useCallback, useEffect, useState } from "react"

/**
 * Disables an action for a fixed period after it is triggered, and counts the remainder
 * down so the control can say why it is unavailable rather than merely being greyed out.
 *
 * The deadline is an absolute timestamp rather than a decrementing counter: a browser
 * throttles timers in a background tab, so counting ticks would drift and leave a button
 * disabled well past its cooldown. Reading the wall clock on each tick means a tab that
 * was backgrounded for the whole period comes back already released.
 */
function useCooldown(durationMs: number) {
  const [endsAt, setEndsAt] = useState<number | null>(null)
  const [remainingMs, setRemainingMs] = useState(0)

  useEffect(() => {
    if (endsAt === null) return

    // Faster than the second it displays, so the visible number never appears to skip.
    const id = setInterval(() => {
      const remaining = endsAt - Date.now()
      if (remaining <= 0) {
        setEndsAt(null)
        setRemainingMs(0)
        return
      }
      setRemainingMs(remaining)
    }, 250)

    return () => clearInterval(id)
  }, [endsAt])

  const start = useCallback(() => {
    setEndsAt(Date.now() + durationMs)
    setRemainingMs(durationMs)
  }, [durationMs])

  return {
    isCoolingDown: endsAt !== null,
    remainingSeconds: Math.ceil(remainingMs / 1000),
    start,
  }
}

export { useCooldown }
