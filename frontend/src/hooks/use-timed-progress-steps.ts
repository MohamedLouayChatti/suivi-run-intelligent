"use client"

import { useEffect, useState } from "react"

interface TimedProgressStep {
  /** Earliest moment, in milliseconds after the operation started, at which this label may show. */
  after: number
  label: string
}

interface UseTimedProgressStepsOptions {
  steps: TimedProgressStep[]
  /** True for exactly as long as the operation is in flight. */
  isActive: boolean
  /** When to admit the operation is taking longer than it usually does. Omit for never. */
  slowAfterMs?: number
}

/**
 * Narrates a long request the backend sends no progress for.
 *
 * Several operations in this product are one HTTP request that takes many seconds — creating a
 * ticket embeds its description and searches the corpus before it answers, and a batch import
 * does that once per row. The backend has no channel to report a phase on, so there is nothing
 * to display but the fact that we are still waiting, which is what made a slow save look like a
 * broken button.
 *
 * The one rule that keeps this honest: **the timer decides only the earliest moment a message
 * may appear, never that anything finished.** Steps advance forward and the last one holds for
 * as long as the request takes, so a slower-than-expected response runs out of messages rather
 * than out of truth; a faster one is answered while an early step is still showing and simply
 * ends the sequence there. Nothing here ever claims a phase completed, because nothing here can
 * know that.
 *
 * The schedule depends on the steps' offsets rather than on the array holding them, so a caller
 * may build the list inline without every render tearing down and restarting its own timers.
 */
function useTimedProgressSteps({ steps, isActive, slowAfterMs }: UseTimedProgressStepsOptions) {
  const [index, setIndex] = useState(0)
  const [isSlow, setIsSlow] = useState(false)
  const [runningFor, setRunningFor] = useState(isActive)

  // React's documented "adjust state when a prop changes" pattern rather than an effect: a new
  // run has to start from the first step instead of wherever the previous one stopped, and doing
  // that during render means the stale step is never painted for a frame first.
  if (runningFor !== isActive) {
    setRunningFor(isActive)
    setIndex(0)
    setIsSlow(false)
  }

  const offsetKey = steps.map((step) => step.after).join(",")

  useEffect(() => {
    if (!isActive) return
    // The first step needs no timer: it is what shows the moment the operation starts.
    const timers = offsetKey
      .split(",")
      .slice(1)
      .map((after, position) => window.setTimeout(() => setIndex(position + 1), Number(after)))
    if (slowAfterMs !== undefined) {
      timers.push(window.setTimeout(() => setIsSlow(true), slowAfterMs))
    }
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [isActive, slowAfterMs, offsetKey])

  return {
    label: isActive ? (steps[Math.min(index, steps.length - 1)]?.label ?? null) : null,
    isSlow: isActive && isSlow,
  }
}

export { useTimedProgressSteps }
export type { TimedProgressStep }
