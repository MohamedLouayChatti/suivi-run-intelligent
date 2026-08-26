/**
 * Single boundary for authentication. Clerk is only imported inside this folder —
 * everything else (HTTP client, feature hooks, components) consumes it from here.
 */
export { AuthTokenBridge } from "./auth-token-bridge";
export { getAuthToken } from "./token-registry";
export { AuthFailureBridge } from "./auth-failure-bridge";
export { notifyAuthFailure } from "./auth-failure-registry";
export { useAuthSession } from "./use-auth-session";
export type { AuthSession } from "./use-auth-session";
export { useCurrentUser, currentUserQueryKey } from "./use-current-user";
export { AuthGate } from "./auth-gate";
export { useLogout } from "./use-logout";
export { usePermissions } from "./use-permissions";
export { RequireRouteAccess } from "./require-permission";
export { buildPermissionGraph } from "./permission-graph";
export type { PermissionGraph } from "./permission-graph";
export { groupPermissions } from "./permission-groups";
export type { PermissionGroup } from "./permission-groups";
