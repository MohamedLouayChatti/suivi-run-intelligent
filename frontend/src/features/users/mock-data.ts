import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]

// Placeholder roles mirroring the real seeded catalog
// (app/scripts/seeding/roles_permissions/roles.py). Replace with a real
// services/api/roles.ts call once it exists.
const mockRoles: RoleResponse[] = [
  { id: "10000000-0000-0000-0000-000000000001", name: "Admin", permission_ids: [] },
  { id: "10000000-0000-0000-0000-000000000002", name: "Support Engineer", permission_ids: [] },
  {
    id: "10000000-0000-0000-0000-000000000003",
    name: "Support Engineer Supervisor",
    permission_ids: [],
  },
]

// `last_active_label`/`member_since_label` are display-only mock fields — the backend
// UserResponse schema doesn't track activity/membership dates yet, and baking fixed
// labels (rather than computing "x min ago" from a stored timestamp at render time)
// keeps this placeholder deterministic between server and client renders.
type MockUser = UserResponse & {
  last_active_label: string | null
  member_since_label: string
}

// Placeholder users for the admin Users page. Replace with a real services/api/users.ts
// call once it exists — consumers only depend on UserResponse[], so swapping the source
// is a one-line change.
const mockUsers: MockUser[] = [
  {
    id: "20000000-0000-0000-0000-000000000001",
    auth_provider_user_id: "user_amelie_moreau",
    email: "amelie.moreau@example.com",
    display_name: "Amélie Moreau",
    active: true,
    role_ids: [mockRoles[2].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "SUPPORT",
    application_assignments: [{ application: "FCI", assignment_type: "PRIMARY" }],
    last_active_label: "il y a 8 min",
    member_since_label: "14 mars 2024",
  },
  {
    id: "20000000-0000-0000-0000-000000000002",
    auth_provider_user_id: "user_luc_fontaine",
    email: "luc.fontaine@example.com",
    display_name: "Luc Fontaine",
    active: true,
    role_ids: [mockRoles[1].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "SUPPORT",
    application_assignments: [
      { application: "COLORIS", assignment_type: "PRIMARY" },
      { application: "FCI", assignment_type: "BACKUP" },
    ],
    last_active_label: "il y a 22 min",
    member_since_label: "2 mai 2024",
  },
  {
    id: "20000000-0000-0000-0000-000000000003",
    auth_provider_user_id: "user_kenji_nakamura",
    email: "kenji.nakamura@example.com",
    display_name: "Kenji Nakamura",
    active: true,
    role_ids: [mockRoles[1].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "SUPPORT",
    application_assignments: [{ application: "AERO", assignment_type: "PRIMARY" }],
    last_active_label: "il y a 1 h",
    member_since_label: "18 juin 2024",
  },
  {
    id: "20000000-0000-0000-0000-000000000004",
    auth_provider_user_id: "user_rafael_silva",
    email: "rafael.silva@example.com",
    display_name: "Rafael Silva",
    active: false,
    role_ids: [mockRoles[1].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "SUPPORT",
    application_assignments: [{ application: "VIO", assignment_type: "PRIMARY" }],
    last_active_label: null,
    member_since_label: "28 juillet 2026",
  },
  {
    id: "20000000-0000-0000-0000-000000000005",
    auth_provider_user_id: "user_mona_haddad",
    email: "mona.haddad@example.com",
    display_name: "Mona Haddad",
    active: true,
    role_ids: [mockRoles[0].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "CONFIGURATION",
    application_assignments: [{ application: "FCI", assignment_type: "PRIMARY" }],
    last_active_label: "il y a 3 min",
    member_since_label: "2 novembre 2023",
  },
  {
    id: "20000000-0000-0000-0000-000000000006",
    auth_provider_user_id: "user_sade_okafor",
    email: "sade.okafor@example.com",
    display_name: "Sade Okafor",
    active: true,
    role_ids: [mockRoles[1].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "CONFIGURATION",
    application_assignments: [{ application: "COLORIS", assignment_type: "PRIMARY" }],
    last_active_label: "il y a 15 min",
    member_since_label: "9 août 2024",
  },
  {
    id: "20000000-0000-0000-0000-000000000007",
    auth_provider_user_id: "user_yanis_belkacem",
    email: "yanis.belkacem@example.com",
    display_name: "Yanis Belkacem",
    active: false,
    role_ids: [mockRoles[1].id],
    direct_permission_ids: [],
    revoked_permission_ids: [],
    functional_team: "SUPPORT",
    application_assignments: [{ application: "AERO", assignment_type: "PRIMARY" }],
    last_active_label: "il y a 12 jours",
    member_since_label: "20 janvier 2024",
  },
]

function getRoleName(user: UserResponse, roles: RoleResponse[]): string {
  return roles.find((r) => user.role_ids.includes(r.id))?.name ?? "—"
}

export { mockRoles, mockUsers, getRoleName }
export type { MockUser }
