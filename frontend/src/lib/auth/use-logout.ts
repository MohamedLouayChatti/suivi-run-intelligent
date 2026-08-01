"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { useClerk } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";

/**
 * The one place the logout sequence is defined: Clerk sign-out, then clear the
 * TanStack Query cache (which drops the cached current user along with it),
 * then redirect to login. Feature code triggers this instead of touching Clerk.
 */
function useLogout(): () => Promise<void> {
  const { signOut } = useClerk();
  const queryClient = useQueryClient();
  const router = useRouter();

  return useCallback(async () => {
    await signOut();
    queryClient.clear();
    router.push("/login");
  }, [signOut, queryClient, router]);
}

export { useLogout };
