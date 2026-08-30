"use client"

import { useCallback, useEffect, useRef } from "react"

import { useCurrentUser } from "@/lib/auth"
import type { CurrentUser } from "@/services/api/auth"

/** How often the application is re-asked whether the change has reached it. */
const SYNC_POLL_INTERVAL_MS = 1_000

/**
 * How long to keep asking before reporting the change as not yet synchronized.
 *
 * A bound rather than a promise: the webhook usually lands in well under a second, and
 * giving up says only "not yet", never "it failed". Svix retries on its own, and the 60s
 * stale time plus the refetch on window focus pick up whatever arrives afterwards.
 */
const SYNC_TIMEOUT_MS = 15_000

/**
 * Waits until a profile change made at the identity provider has reached this application.
 *
 * Everything on the Paramètres page writes to Clerk, and Clerk reaches our database only
 * afterwards, through the `user.updated` webhook. So the write resolving means the *provider*
 * accepted it, not that anything the app renders has changed — the header reads `/auth/me`,
 * which is our own database. Invalidating that query when the write resolves loses the race
 * essentially every time and refetches the old value; patching the cache with the new one
 * would show a name that may never have reached the database at all, which is the failure
 * this exists to avoid.
 *
 * So neither: the submitted value is verified rather than assumed. `hasLanded` is asked of
 * each refetched profile, and the caller learns which of the two outcomes it got — reached
 * the application, or accepted by the provider and still on its way. The predicate compares
 * what was submitted, never a composed display name: composing one is a backend rule, and
 * the whole point of this change was to stop the frontend having a second opinion about it.
 */
function useProfileSync() {
  const { refetch } = useCurrentUser()
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

  return useCallback(
    async function waitForSync(hasLanded: (user: CurrentUser) => boolean): Promise<boolean> {
      const deadline = Date.now() + SYNC_TIMEOUT_MS
      while (Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, SYNC_POLL_INTERVAL_MS))
        if (!isMounted.current) return false
        const { data } = await refetch()
        if (data && hasLanded(data)) return true
      }
      return false
    },
    [refetch],
  )
}

export { useProfileSync }
