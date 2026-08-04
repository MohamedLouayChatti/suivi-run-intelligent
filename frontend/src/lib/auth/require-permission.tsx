"use client";

import type { ReactNode } from "react";

import { AccessDeniedScreen } from "@/components/app/access-denied";

import { usePermissions } from "./use-permissions";

interface RequirePermissionProps {
  /** Hard admin-role gate — for collection/reference-data-wide pages (mirrors `require_admin`). */
  admin?: boolean;
  /** A single permission name the current user's effective permissions must include. */
  permission?: string;
  children: ReactNode;
}

/**
 * Route-level permission-aware UX: renders an Access-Denied screen instead of the page when the
 * current user is known to lack access, rather than silently redirecting. Always runs inside
 * AuthGate, so the current user is already resolved here.
 */
function RequirePermission({ admin, permission, children }: RequirePermissionProps) {
  const { isAdmin, hasPermission } = usePermissions();

  const allowed = (!admin || isAdmin) && (!permission || hasPermission(permission));

  if (!allowed) {
    return <AccessDeniedScreen />;
  }

  return <>{children}</>;
}

export { RequirePermission };
