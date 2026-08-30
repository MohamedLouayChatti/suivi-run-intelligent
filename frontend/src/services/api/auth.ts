import type { components } from "@/types/api";

import { httpClient } from "./client";

type MeResponse = components["schemas"]["MeResponse"];

interface CurrentUserRole {
  id: string;
  name: string;
}

interface CurrentUserPermission {
  id: string;
  name: string;
}

interface CurrentUserApplicationAssignment {
  application: components["schemas"]["Application"];
  assignmentType: components["schemas"]["AssignmentType"];
}

/**
 * The app's clean, camelCase view of the authenticated user — the shape feature
 * code and presentation components see. Never the raw generated MeResponse.
 */
interface CurrentUser {
  id: string;
  authProviderUserId: string;
  email: string;
  firstName: string;
  lastName: string;
  /**
   * The composed full name, as the backend writes it. Read it; never build it from
   * `firstName` and `lastName` here — which half leads is a rule the backend owns, and
   * composing it in React is exactly how the settings form and the header came to disagree.
   */
  displayName: string;
  avatarUrl: string | null;
  functionalTeam: components["schemas"]["FunctionalTeam"];
  applicationAssignments: CurrentUserApplicationAssignment[];
  role: CurrentUserRole;
  effectivePermissions: CurrentUserPermission[];
}

function toCurrentUser(response: MeResponse): CurrentUser {
  return {
    id: response.id,
    authProviderUserId: response.auth_provider_user_id,
    email: response.email,
    firstName: response.first_name,
    lastName: response.last_name,
    displayName: response.display_name,
    avatarUrl: response.avatar_url,
    functionalTeam: response.functional_team,
    applicationAssignments: response.application_assignments.map((assignment) => ({
      application: assignment.application,
      assignmentType: assignment.assignment_type,
    })),
    role: { id: response.role.id, name: response.role.name },
    effectivePermissions: response.effective_permissions.map((permission) => ({
      id: permission.id,
      name: permission.name,
    })),
  };
}

/** Fetches the application's representation of the authenticated user — GET /auth/me. */
async function getCurrentUser(): Promise<CurrentUser> {
  const { data } = await httpClient.get<MeResponse>("/auth/me");
  return toCurrentUser(data);
}

function getPrimaryApplication(user: CurrentUser): components["schemas"]["Application"] | null {
  return (
    user.applicationAssignments.find((a) => a.assignmentType === "PRIMARY")?.application ?? null
  );
}

function getBackupApplication(user: CurrentUser): components["schemas"]["Application"] | null {
  return (
    user.applicationAssignments.find((a) => a.assignmentType === "BACKUP")?.application ?? null
  );
}

/**
 * Applications the user has *reach* into — every assignment regardless of type, including
 * READ_ONLY. Mirrors `has_application_assignment`: what scopes a list/filter view (tickets,
 * history, analytics) and what lets someone comment on a ticket, never what lets them act on
 * one. For ticket-creation eligibility, use `getActionableApplications` instead.
 */
function getAccessibleApplications(user: CurrentUser): components["schemas"]["Application"][] {
  return [...new Set(user.applicationAssignments.map((a) => a.application))];
}

/**
 * Applications the user is *staffed* on — their primary, plus backup if they have one. Mirrors
 * `has_actionable_application_assignment`: excludes READ_ONLY, since that assignment grants
 * reach without staffing. Use this to gate ticket creation, never `getAccessibleApplications`.
 */
function getActionableApplications(user: CurrentUser): components["schemas"]["Application"][] {
  const primary = getPrimaryApplication(user);
  const backup = getBackupApplication(user);
  return [primary, backup].filter((a): a is components["schemas"]["Application"] => a !== null);
}

export {
  getCurrentUser,
  getPrimaryApplication,
  getBackupApplication,
  getAccessibleApplications,
  getActionableApplications,
};
export type { CurrentUser, CurrentUserApplicationAssignment, CurrentUserPermission, CurrentUserRole };
