import { getAccessibleApplications, isAdmin as isAdminUser } from "@/services/api/auth";
import type { CurrentUser } from "@/services/api/auth";
import type { components } from "@/types/api";

type Application = components["schemas"]["Application"];

/**
 * Pure, framework-free permission checks over `CurrentUser`. Each mirrors a rule read directly
 * from the backend's instance authorization policies — for hiding UI only, never a substitute
 * for the backend's own enforcement.
 */
function hasPermission(user: CurrentUser | undefined, name: string): boolean {
  return user?.effectivePermissions.some((permission) => permission.name === name) ?? false;
}

function isTicketAssignee(
  user: CurrentUser | undefined,
  ticket: { assignee: { id: string } | null }
): boolean {
  return user !== undefined && ticket.assignee !== null && ticket.assignee.id === user.id;
}

function isCommentAuthor(
  user: CurrentUser | undefined,
  comment: { author: { id: string } | null }
): boolean {
  return user !== undefined && comment.author !== null && comment.author.id === user.id;
}

function isAttachmentUploader(
  user: CurrentUser | undefined,
  attachment: { uploader: { id: string } | null }
): boolean {
  return user !== undefined && attachment.uploader !== null && attachment.uploader.id === user.id;
}

/** Mirrors `has_application_assignment` — the user's primary/backup application assignments. */
function canActOnApplication(user: CurrentUser | undefined, application: Application): boolean {
  return user !== undefined && getAccessibleApplications(user).includes(application);
}

/** The backend's hard `require_admin` role gate — see `services/api/auth.ts`'s `isAdmin`. */
function isAdmin(user: CurrentUser | undefined): boolean {
  return user !== undefined && isAdminUser(user);
}

export {
  hasPermission,
  isTicketAssignee,
  isCommentAuthor,
  isAttachmentUploader,
  canActOnApplication,
  isAdmin,
};
