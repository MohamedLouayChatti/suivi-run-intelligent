"use client";

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";

import { registerAuthTokenGetter } from "./token-registry";

/**
 * Mounted once near the app root (inside ClerkProvider). Keeps the module-level
 * token registry pointed at Clerk's current `getToken`, so non-component code
 * (the shared Axios client) can fetch a fresh JWT without depending on Clerk directly.
 */
function AuthTokenBridge(): null {
  const { getToken } = useAuth();

  useEffect(() => {
    registerAuthTokenGetter(() => getToken());
  }, [getToken]);

  return null;
}

export { AuthTokenBridge };
