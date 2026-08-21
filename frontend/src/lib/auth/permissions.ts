import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth";
import type { CurrentUser } from "@/services/api/auth";
import type { components } from "@/types/api";

type Application = components["schemas"]["Application"];

/**
 * Pure, framework-free permission checks over `CurrentUser`. Each mirrors a rule read directly
 * from the backend's instance authorization policies — for hiding UI only, never a substitute
 * for the backend's own enforcement.
 *
 * There is deliberately no `isAdmin` here, and nothing in the frontend reads `user.role` to
 * decide what may be done. A role is only a bundle of permissions on the backend, so mapping
 * "role Admin" to a capability would be business logic living in the UI — and it would go
 * stale the moment a permission is granted to another role or directly to one user. Ask for
 * the permission the backend actually enforces instead (including breadth permissions like
 * `user.read_all` or `ticket.manage_any`).
 */
function hasPermission(user: CurrentUser | undefined, name: string): boolean {
  return user?.effectivePermissions.some((permission) => permission.name === name) ?? false;
}

/** Every listed permission must be held — mirrors the backend's conjunctive `require_permissions`. */
function hasAllPermissions(user: CurrentUser | undefined, names: readonly string[]): boolean {
  return names.every((name) => hasPermission(user, name));
}

/**
 * At least one of the listed permissions is held. Not a mirror of any single backend check —
 * `require_permissions` is conjunctive — but of a page that composes several independently
 * gated capabilities: the Knowledge Base admin page carries batch import and recalculation
 * management, each with its own permission and its own backend route. Holding either is reason
 * to see the page; each section then asks for the permission it actually needs.
 */
function hasAnyPermission(user: CurrentUser | undefined, names: readonly string[]): boolean {
  return names.some((name) => hasPermission(user, name));
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

/**
 * Mirrors `has_primary_application_assignment` — the one application the user runs, as opposed
 * to the one they back up. A user has at most one of each; the `User` aggregate refuses any
 * other shape, so there is exactly one answer to compare against here.
 */
function isPrimaryApplication(user: CurrentUser | undefined, application: Application): boolean {
  return user !== undefined && getPrimaryApplication(user) === application;
}

/**
 * Mirrors `may_manage_others_tickets` — whether the user may act on a ticket in `application`
 * that is not assigned to them. Two independent ways to qualify: unrestricted reach anywhere,
 * or reach confined to the one application they run.
 */
function canManageOthersTickets(
  user: CurrentUser | undefined,
  application: Application
): boolean {
  return (
    hasPermission(user, "ticket.manage_any") ||
    (hasPermission(user, "ticket.manage_primary_application") &&
      isPrimaryApplication(user, application))
  );
}

/**
 * Mirrors `BatchImportPolicy` — whether the user may load a file of tickets for `application`.
 * Two independent ways to qualify, neither of them a role: the breadth permission, or the one
 * application they run.
 *
 * A backup assignment deliberately does not qualify, unlike `canActOnApplication` above. Bulk
 * loading an application's historical incidents decides what its whole corpus says and what
 * every future similarity suggestion is drawn from, which is running the project rather than
 * covering it — the same line `canManageOthersTickets` draws.
 */
function canImportForApplication(
  user: CurrentUser | undefined,
  application: Application
): boolean {
  return (
    hasPermission(user, "knowledge_base.import_any_application") ||
    isPrimaryApplication(user, application)
  );
}

export {
  hasPermission,
  hasAllPermissions,
  hasAnyPermission,
  isTicketAssignee,
  isCommentAuthor,
  isAttachmentUploader,
  canActOnApplication,
  isPrimaryApplication,
  canManageOthersTickets,
  canImportForApplication,
};
