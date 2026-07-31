/**
 * Single boundary for authentication. Clerk is only imported inside this folder —
 * everything else (HTTP client, feature hooks, components) consumes it from here.
 */
export { AuthTokenBridge } from "./auth-token-bridge";
export { getAuthToken } from "./token-registry";
export { useAuthSession } from "./use-auth-session";
export type { AuthSession } from "./use-auth-session";
