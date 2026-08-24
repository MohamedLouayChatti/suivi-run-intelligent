"use client";

import { routeRequirements } from "@/components/layout/nav-config";

import {
  canActOnApplication,
  canImportForApplication,
  canManageOthersTickets,
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
  isAttachmentUploader,
  isCommentAuthor,
  isTicketAssignee,
} from "./permissions";
import { useCurrentUser } from "./use-current-user";

/**
 * Permission-aware UX only — reduces visual noise by hiding what the current user is known
 * not to be able to do. Never a security boundary: the backend enforces every one of these
 * rules independently on every request. See `permissions.ts` for the underlying checks.
 */
function usePermissions() {
  const { data: user, isPending: isLoading } = useCurrentUser();

  return {
    user,
    isLoading,
    hasPermission: (name: string) => hasPermission(user, name),
    hasAllPermissions: (names: readonly string[]) => hasAllPermissions(user, names),
    hasAnyPermission: (names: readonly string[]) => hasAnyPermission(user, names),
    /**
     * Whether `href` would open rather than show an Access-Denied screen, read from the same
     * `routeRequirements` the sidebar and `RequireRouteAccess` use. For links that cross into
     * another page — the Dashboard's shortcuts into Analyses, Tickets and Historique — so a
     * button is not offered to somebody the destination will refuse. A route with no declared
     * requirement is open to anyone signed in.
     */
    canAccessRoute: (href: string) => {
      const requirement = routeRequirements[href];
      if (!requirement) return true;
      if (requirement.permission && !hasPermission(user, requirement.permission)) return false;
      if (requirement.anyPermission && !hasAnyPermission(user, requirement.anyPermission)) return false;
      return true;
    },
    isTicketAssignee: (ticket: Parameters<typeof isTicketAssignee>[1]) =>
      isTicketAssignee(user, ticket),
    isCommentAuthor: (comment: Parameters<typeof isCommentAuthor>[1]) =>
      isCommentAuthor(user, comment),
    isAttachmentUploader: (attachment: Parameters<typeof isAttachmentUploader>[1]) =>
      isAttachmentUploader(user, attachment),
    canActOnApplication: (application: Parameters<typeof canActOnApplication>[1]) =>
      canActOnApplication(user, application),
    canManageOthersTickets: (application: Parameters<typeof canManageOthersTickets>[1]) =>
      canManageOthersTickets(user, application),
    canImportForApplication: (application: Parameters<typeof canImportForApplication>[1]) =>
      canImportForApplication(user, application),
  };
}

export { usePermissions };
