/**
 * Module-level bridge from non-component code (the shared Axios client) to the
 * React-only APIs needed to react to a 401 — Clerk's signOut, the TanStack Query
 * cache, and the router. Mirrors token-registry.ts: AuthFailureBridge (mounted
 * once near the app root) registers the handler here; the Axios response
 * interceptor only calls `notifyAuthFailure`.
 */

type AuthFailureHandler = () => void;

let currentHandler: AuthFailureHandler = () => {};

function registerAuthFailureHandler(handler: AuthFailureHandler): void {
  currentHandler = handler;
}

function notifyAuthFailure(): void {
  currentHandler();
}

export { registerAuthFailureHandler, notifyAuthFailure };
export type { AuthFailureHandler };
