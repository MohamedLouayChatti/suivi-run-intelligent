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
  displayName: string;
  functionalTeam: components["schemas"]["FunctionalTeam"];
  applicationAssignments: CurrentUserApplicationAssignment[];
  roles: CurrentUserRole[];
  effectivePermissions: CurrentUserPermission[];
}

function toCurrentUser(response: MeResponse): CurrentUser {
  return {
    id: response.id,
    authProviderUserId: response.auth_provider_user_id,
    email: response.email,
    displayName: response.display_name,
    functionalTeam: response.functional_team,
    applicationAssignments: response.application_assignments.map((assignment) => ({
      application: assignment.application,
      assignmentType: assignment.assignment_type,
    })),
    roles: response.roles.map((role) => ({ id: role.id, name: role.name })),
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

export { getCurrentUser, getPrimaryApplication, getBackupApplication };
export type { CurrentUser, CurrentUserApplicationAssignment, CurrentUserPermission, CurrentUserRole };
