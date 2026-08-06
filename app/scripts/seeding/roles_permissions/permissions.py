from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
	name: str
	description: str


# Keep this catalog ordered and readable: it is the source of truth for
# authorization reference data.  The order is also used for deterministic
# seeding and logging.
PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = (
	PermissionDefinition("user.read", "Lire les informations d'un utilisateur."),
	PermissionDefinition("user.activate", "Activer un utilisateur."),
	PermissionDefinition("user.deactivate", "Désactiver un utilisateur."),
	PermissionDefinition("role.read", "Lire les informations d'un rôle."),
	PermissionDefinition("role.assign", "Attribuer un rôle à un utilisateur."),
	PermissionDefinition("role.revoke", "Retirer un rôle à un utilisateur."),
	PermissionDefinition("permission.read", "Lire les informations d'une permission."),
	PermissionDefinition("permission.grant_to_role", "Accorder une permission à un rôle."),
	PermissionDefinition("permission.revoke_from_role", "Retirer une permission d'un rôle."),
	PermissionDefinition("permission.grant_to_user", "Accorder une permission directement à un utilisateur."),
	PermissionDefinition("permission.revoke_from_user", "Retirer une permission directe d'un utilisateur."),
	PermissionDefinition("ticket.create", "Créer un ticket."),
	PermissionDefinition("ticket.read", "Lire les informations d'un ticket."),
	PermissionDefinition("ticket.assign", "Affecter un ticket."),
	PermissionDefinition("ticket.change_priority", "Changer la priorité d'un ticket."),
	PermissionDefinition("ticket.change_status", "Changer le statut d'un ticket."),
	PermissionDefinition("ticket.transfer_application", "Transférer un ticket vers une autre application."),
	PermissionDefinition("ticket.archive", "Archiver un ticket."),
	PermissionDefinition("ticket.restore", "Restaurer un ticket archivé."),
	PermissionDefinition("comment.create", "Ajouter un commentaire à un ticket."),
	PermissionDefinition("comment.update", "Modifier un commentaire."),
	PermissionDefinition("comment.delete", "Supprimer un commentaire."),
	PermissionDefinition("attachment.create", "Ajouter une pièce jointe."),
	PermissionDefinition("attachment.delete", "Supprimer une pièce jointe."),
	PermissionDefinition("attachment.read", "Télécharger une pièce jointe."),
	PermissionDefinition("audit.read", "Lire les entrées du journal d'audit."),
	PermissionDefinition("notification.read", "Lire ses propres notifications."),
)

PERMISSIONS_BY_NAME = {permission.name: permission for permission in PERMISSION_CATALOG}
