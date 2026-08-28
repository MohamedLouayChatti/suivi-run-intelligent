"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/services/api/auth";

import { useAuthSession } from "./use-auth-session";

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
  });
}

export { currentUserQueryKey, useCurrentUser };
