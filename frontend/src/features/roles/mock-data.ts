import type { components } from "@/types/api"

type PermissionResponse = components["schemas"]["PermissionResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]

// Placeholder permission catalog mirroring the real seeded reference data
// (app/scripts/seeding/roles_permissions/permissions.py). Replace with a real
// services/api/permissions.ts call once it exists.
const mockPermissions: PermissionResponse[] = [
  { id: "30000000-0000-0000-0000-000000000001", name: "user.read", description: "Lire les informations utilisateur." },
  { id: "30000000-0000-0000-0000-000000000002", name: "user.activate", description: "Activer un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000003", name: "user.deactivate", description: "Désactiver un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000004", name: "role.read", description: "Lire les informations d'un rôle." },
  { id: "30000000-0000-0000-0000-000000000005", name: "role.assign", description: "Attribuer un rôle à un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000006", name: "role.revoke", description: "Retirer un rôle à un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000007", name: "permission.read", description: "Lire les informations d'une permission." },
  { id: "30000000-0000-0000-0000-000000000008", name: "permission.grant_to_role", description: "Accorder une permission à un rôle." },
  { id: "30000000-0000-0000-0000-000000000009", name: "permission.revoke_from_role", description: "Retirer une permission d'un rôle." },
  { id: "30000000-0000-0000-0000-000000000010", name: "permission.grant_to_user", description: "Accorder une permission directement à un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000011", name: "permission.revoke_from_user", description: "Retirer une permission directe d'un utilisateur." },
  { id: "30000000-0000-0000-0000-000000000012", name: "ticket.create", description: "Créer un ticket." },
  { id: "30000000-0000-0000-0000-000000000013", name: "ticket.read", description: "Lire les informations d'un ticket." },
  { id: "30000000-0000-0000-0000-000000000014", name: "ticket.assign", description: "Assigner un ticket." },
  { id: "30000000-0000-0000-0000-000000000015", name: "ticket.change_priority", description: "Changer la priorité d'un ticket." },
  { id: "30000000-0000-0000-0000-000000000016", name: "ticket.change_status", description: "Changer le statut d'un ticket." },
  { id: "30000000-0000-0000-0000-000000000017", name: "ticket.transfer_application", description: "Transférer un ticket vers une autre application." },
  { id: "30000000-0000-0000-0000-000000000018", name: "ticket.archive", description: "Archiver un ticket." },
  { id: "30000000-0000-0000-0000-000000000019", name: "ticket.restore", description: "Restaurer un ticket archivé." },
  { id: "30000000-0000-0000-0000-000000000020", name: "comment.create", description: "Ajouter un commentaire à un ticket." },
  { id: "30000000-0000-0000-0000-000000000021", name: "comment.update", description: "Modifier un commentaire." },
  { id: "30000000-0000-0000-0000-000000000022", name: "comment.delete", description: "Supprimer un commentaire." },
  { id: "30000000-0000-0000-0000-000000000023", name: "attachment.create", description: "Ajouter une pièce jointe." },
  { id: "30000000-0000-0000-0000-000000000024", name: "attachment.delete", description: "Supprimer une pièce jointe." },
]

function permissionIds(names: string[]): string[] {
  return names.map((name) => mockPermissions.find((p) => p.name === name)!.id)
}

// `description`/`last_modified_label` are display-only mock fields — RoleResponse
// doesn't carry them yet, and role management (create/edit) isn't part of this app;
// roles are seeded, not authored by admins.
type MockRole = RoleResponse & {
  description: string
  last_modified_label: string
}

// Placeholder roles mirroring the real seeded catalog
// (app/scripts/seeding/roles_permissions/roles.py). Replace with a real
// services/api/roles.ts call once it exists. Kept in sync with the Users page,
// which imports `mockRoles` from here rather than defining its own copy.
const mockRoles: MockRole[] = [
  {
    id: "10000000-0000-0000-0000-000000000001",
    name: "Admin",
    permission_ids: mockPermissions.map((p) => p.id),
    description: "Accès complet à la plateforme, y compris l'administration des utilisateurs, des rôles et des permissions.",
    last_modified_label: "12 juil. 2026",
  },
  {
    id: "10000000-0000-0000-0000-000000000002",
    name: "Support Engineer",
    permission_ids: permissionIds([
      "user.read",
      "role.read",
      "ticket.read",
      "ticket.assign",
      "ticket.change_priority",
      "ticket.change_status",
      "ticket.transfer_application",
      "ticket.archive",
      "ticket.restore",
      "comment.create",
      "comment.update",
      "comment.delete",
      "attachment.create",
      "attachment.delete",
    ]),
    description: "Prend en charge la résolution des tickets au quotidien et la contribution aux connaissances.",
    last_modified_label: "3 juin 2026",
  },
  {
    id: "10000000-0000-0000-0000-000000000003",
    name: "Support Engineer Supervisor",
    permission_ids: [],
    description: "Supervise les files d'attente, réassigne le travail et consulte les analyses opérationnelles.",
    last_modified_label: "22 mars 2025",
  },
]

export { mockPermissions, mockRoles }
export type { MockRole }
