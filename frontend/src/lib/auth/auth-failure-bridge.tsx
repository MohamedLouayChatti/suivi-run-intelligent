"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useClerk } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";

import { registerAuthFailureHandler } from "./auth-failure-registry";

/**
 * Mounted once near the app root (inside ClerkProvider + QueryClientProvider).
 * Registers the 401 handler the shared Axios client falls back to: a rejected
 * backend token means the session is no longer valid, so both auth layers are
 * torn down together — Clerk sign-out, then the query cache, then a redirect
 * to login — rather than leaving a stale Clerk session behind.
 */
function AuthFailureBridge(): null {
  const { signOut } = useClerk();
  const queryClient = useQueryClient();
  const router = useRouter();
  const isHandling = useRef(false);

  useEffect(() => {
    registerAuthFailureHandler(() => {
      if (isHandling.current) return;
      isHandling.current = true;

      void signOut().finally(() => {
        queryClient.clear();
        router.push("/login");
        isHandling.current = false;
      });
    });
  }, [signOut, queryClient, router]);

  return null;
}

export { AuthFailureBridge };
