import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]
type Application = components["schemas"]["Application"]

// Placeholder until Clerk/session wiring + services/api/users.ts exist.
// Replace the body of this hook with a real fetch — consumers only depend on the return shape.
const mockCurrentUser: UserResponse = {
  id: "00000000-0000-0000-0000-000000000001",
  auth_provider_user_id: "user_placeholder",
  email: "engineer@example.com",
  display_name: "Camille Martin",
  active: true,
  role_ids: [],
  direct_permission_ids: [],
  revoked_permission_ids: [],
  functional_team: "SUPPORT",
  application_assignments: [
    { application: "FCI", assignment_type: "PRIMARY" },
    { application: "VIO", assignment_type: "BACKUP" },
  ],
}

function useCurrentUser(): UserResponse {
  return mockCurrentUser
}

function getPrimaryApplication(user: UserResponse): Application | null {
  return (
    user.application_assignments.find((a) => a.assignment_type === "PRIMARY")
      ?.application ?? null
  )
}

function getBackupApplication(user: UserResponse): Application | null {
  return (
    user.application_assignments.find((a) => a.assignment_type === "BACKUP")
      ?.application ?? null
  )
}

export { useCurrentUser, getPrimaryApplication, getBackupApplication }
