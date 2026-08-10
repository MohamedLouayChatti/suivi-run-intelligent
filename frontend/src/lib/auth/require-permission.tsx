"use client";

import type { ReactNode } from "react";

import { AccessDeniedScreen } from "@/components/app/access-denied";

import { usePermissions } from "./use-permissions";

interface RequirePermissionProps {
  /** A single permission name the current user's effective permissions must include. */
  permission?: string;
  /** Several permission names, all of which must be held — mirrors `require_permissions`. */
  permissions?: readonly string[];
  children: ReactNode;
}

/**
 * Route-level permission-aware UX: renders an Access-Denied screen instead of the page when the
 * current user is known to lack access, rather than silently redirecting. Always runs inside
 * AuthGate, so the current user is already resolved here.
 *
 * Gates are always permission names — never roles. Pages that used to be "admin only" now name
 * the breadth permission the backend actually checks (`user.read_all`, `role.read_all`,
 * `audit.read`, …), so granting that permission to another role, or directly to one user, opens
 * the page without any frontend change.
 */
function RequirePermission({ permission, permissions, children }: RequirePermissionProps) {
  const { hasPermission, hasAllPermissions } = usePermissions();

  const allowed =
    (permission === undefined || hasPermission(permission)) &&
    (permissions === undefined || hasAllPermissions(permissions));

  if (!allowed) {
    return <AccessDeniedScreen />;
  }

  return <>{children}</>;
}

export { RequirePermission };
