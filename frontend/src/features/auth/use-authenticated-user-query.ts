"use client";

import { useQuery } from "@tanstack/react-query";

import { useAuthSession } from "@/lib/auth";
import { getCurrentUser } from "@/services/api/auth";

/**
 * Foundation for the future Clerk session -> JWT -> GET /auth/me -> UI flow.
 * Not consumed anywhere yet — src/hooks/use-current-user.ts (mock data) still
 * drives existing pages. This is what will replace it once pages are migrated.
 */
const authenticatedUserQueryKey = ["auth", "me"] as const;

function useAuthenticatedUserQuery() {
  const { isSignedIn } = useAuthSession();

  return useQuery({
    queryKey: authenticatedUserQueryKey,
    queryFn: getCurrentUser,
    enabled: isSignedIn,
  });
}

export { authenticatedUserQueryKey, useAuthenticatedUserQuery };
