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
	PermissionDefinition("user.read_all", "Lire les informations de tous les utilisateurs."),
	PermissionDefinition("user.activate", "Activer un utilisateur."),
	PermissionDefinition("user.deactivate", "Désactiver un utilisateur."),
	PermissionDefinition("role.read", "Lire les informations d'un rôle."),
	PermissionDefinition("role.read_all", "Lire les informations de tous les rôles."),
	PermissionDefinition("role.assign", "Attribuer un rôle à un utilisateur."),
	PermissionDefinition("role.revoke", "Retirer un rôle à un utilisateur."),
	PermissionDefinition("permission.read", "Lire les informations d'une permission."),
	PermissionDefinition("permission.grant_to_role", "Accorder une permission à un rôle."),
	PermissionDefinition("permission.revoke_from_role", "Retirer une permission d'un rôle."),
	PermissionDefinition("permission.grant_to_user", "Accorder une permission directement à un utilisateur."),
	PermissionDefinition("permission.revoke_from_user", "Retirer une permission directe d'un utilisateur."),
	PermissionDefinition("ticket.create", "Créer un ticket."),
	PermissionDefinition("ticket.read", "Lire les informations d'un ticket."),
	PermissionDefinition("ticket.read_any_application", "Consulter les tickets de toutes les applications, au-delà de ses propres affectations."),
	PermissionDefinition("ticket.manage_any", "Agir sur un ticket dont on n'est pas l'assigné."),
	PermissionDefinition("ticket.assign", "Affecter un ticket."),
	PermissionDefinition("ticket.change_priority", "Changer la priorité d'un ticket."),
	PermissionDefinition("ticket.change_status", "Changer le statut d'un ticket."),
	PermissionDefinition("ticket.manage_jira", "Gérer les informations Jira d'un ticket."),
	PermissionDefinition("ticket.manage_highlight", "Gérer le point d'attention opérationnel d'un ticket."),
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
	PermissionDefinition("analytics.read", "Lire les indicateurs et statistiques analytiques."),
	PermissionDefinition("analytics.read_any_application", "Consulter les analyses de toutes les applications (vue transverse)."),
	PermissionDefinition("knowledge_base.read_recalculation", "Consulter la planification du recalcul complet du graphe de similarité."),
	PermissionDefinition("knowledge_base.manage_recalculation", "Modifier la planification du recalcul complet du graphe de similarité et le déclencher manuellement."),
)

PERMISSIONS_BY_NAME = {permission.name: permission for permission in PERMISSION_CATALOG}
