"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/services/api/auth";
import { ApiError } from "@/services/api/errors";

import { useAuthSession } from "./use-auth-session";

/**
 * How often a deactivated account re-asks whether it has been activated.
 *
 * Polling is the only mechanism available here, and deliberately so rather than for
 * want of a push channel: the notification stream needs an authenticated connection,
 * and /auth/me answering 403 is precisely the state in which this user has none. The
 * activation notification is written and delivered to nobody.
 */
const DEACTIVATED_POLL_INTERVAL_MS = 15_000;

/**
 * GET /auth/me is the only canonical source of application user identity —
 * never read display name, email, roles, permissions, or application
 * assignments from Clerk. Enabled only once Clerk itself reports a session,
 * so it never fires for anonymous visitors on public routes.
 */
const currentUserQueryKey = ["auth", "me"] as const;

/**
 * The GET /auth/me query result (data/isPending/isError/error/refetch), and the only source of
 * the signed-in user anywhere in the app — the placeholder hook that pages once rendered from is
 * gone, along with the last of the mock data it belonged to.
 */
function useCurrentUser() {
  const { isSignedIn } = useAuthSession();

  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: getCurrentUser,
    enabled: isSignedIn,
    // Self-arming, and self-disarming: the interval is recomputed on every state
    // change, so a query falling into 403 starts polling and one that succeeds returns
    // false and stops. A deactivated user therefore sits on "Accès refusé" and watches
    // it become the application when an administrator activates them, rather than
    // having to know to refresh — which they have no way of knowing.
    //
    // `retry: false` on 4xx leaves this query parked in an error state; the interval
    // runs regardless, error state not being one of the conditions that clears it. It
    // ticks only while the tab is focused, so a backgrounded one costs nothing.
    refetchInterval: (query) =>
      query.state.error instanceof ApiError && query.state.error.status === 403
        ? DEACTIVATED_POLL_INTERVAL_MS
        : false,
  });
}

export { currentUserQueryKey, useCurrentUser };
