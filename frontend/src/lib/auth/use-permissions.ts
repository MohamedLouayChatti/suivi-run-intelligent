"use client";

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
