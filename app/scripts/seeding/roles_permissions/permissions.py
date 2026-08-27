from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
	name: str
	description: str
	requires: tuple[str, ...] = ()
	"""The permissions that must be held for this one to be usable at all.

	A capability presupposes the reach that makes it reachable: `user.activate` is inert
	without `user.read_all`, because nothing else puts a user in front of the caller to
	activate.  Declared here rather than inferred, for the same reason
	`Role.requires_primary_application` is declared: it is a statement about what the
	permission *means*, and no amount of reading its name or its holders recovers it.

	Conjunctive -- every listed name must be held, matching `require_permissions`.  Applied
	transitively, so `ticket.manage_any` needing `ticket.read_any_application` also needs
	`ticket.read`, without restating it.  The graph must stay acyclic; the seeder refuses to
	run otherwise, and refuses a seeded role that is not closed under it.
	"""


# Keep this catalog ordered and readable: it is the source of truth for
# authorization reference data.  The order is also used for deterministic
# seeding and logging.
PERMISSION_CATALOG: tuple[PermissionDefinition, ...] = (
	PermissionDefinition("user.read", "Lire les informations d'un utilisateur."),
	PermissionDefinition("user.read_all", "Lire les informations de tous les utilisateurs.", requires=("user.read",)),
	PermissionDefinition("user.activate", "Activer un utilisateur.", requires=("user.read_all",)),
	PermissionDefinition("user.deactivate", "Désactiver un utilisateur.", requires=("user.read_all",)),
	PermissionDefinition("user.manage_organization", "Gérer l'affectation applicative et l'équipe fonctionnelle d'un utilisateur.", requires=("user.read_all",)),
	PermissionDefinition("role.read", "Lire les informations d'un rôle."),
	PermissionDefinition("role.read_all", "Lire les informations de tous les rôles.", requires=("role.read",)),
	# Assigning a role needs both lists: the roles to choose from, and the user to apply it to.
	PermissionDefinition("role.assign", "Définir le rôle d'un utilisateur.", requires=("role.read_all", "user.read_all")),
	PermissionDefinition("permission.read", "Lire les informations d'une permission."),
	PermissionDefinition("permission.grant_to_role", "Accorder une permission à un rôle.", requires=("role.read_all", "permission.read")),
	PermissionDefinition("permission.revoke_from_role", "Retirer une permission d'un rôle.", requires=("role.read_all", "permission.read")),
	PermissionDefinition("permission.grant_to_user", "Accorder une permission directement à un utilisateur.", requires=("user.read_all", "permission.read")),
	PermissionDefinition("permission.revoke_from_user", "Retirer une permission directe d'un utilisateur.", requires=("user.read_all", "permission.read")),
	PermissionDefinition("ticket.create", "Créer un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.read", "Lire les informations d'un ticket."),
	PermissionDefinition("ticket.read_any_application", "Consulter les tickets de toutes les applications, au-delà de ses propres affectations.", requires=("ticket.read",)),
	# Acting on any application's tickets presupposes being able to read them there, which is
	# what chains this to `ticket.read` without naming it twice.
	PermissionDefinition("ticket.manage_any", "Agir sur un ticket dont on n'est pas l'assigné, toutes applications confondues.", requires=("ticket.read_any_application",)),
	# Deliberately *not* `ticket.read_any_application`: this reach stops at the application the
	# holder runs, which their own assignment already lets them read.
	PermissionDefinition("ticket.manage_primary_application", "Agir sur un ticket dont on n'est pas l'assigné, au sein de son application principale.", requires=("ticket.read",)),
	# `user.read` is what opens the user directory, i.e. the list an assignee is picked from.
	PermissionDefinition("ticket.assign", "Affecter un ticket.", requires=("ticket.read", "user.read")),
	PermissionDefinition("ticket.change_priority", "Changer la priorité d'un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.change_status", "Changer le statut d'un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.manage_jira", "Gérer les informations Jira d'un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.manage_highlight", "Gérer le point d'attention opérationnel d'un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.transfer_application", "Transférer un ticket vers une autre application.", requires=("ticket.read",)),
	PermissionDefinition("ticket.archive", "Archiver un ticket.", requires=("ticket.read",)),
	PermissionDefinition("ticket.restore", "Restaurer un ticket archivé.", requires=("ticket.read",)),
	PermissionDefinition("comment.create", "Ajouter un commentaire à un ticket.", requires=("ticket.read",)),
	PermissionDefinition("comment.update", "Modifier un commentaire.", requires=("ticket.read",)),
	PermissionDefinition("comment.delete", "Supprimer un commentaire.", requires=("ticket.read",)),
	PermissionDefinition("attachment.create", "Ajouter une pièce jointe.", requires=("ticket.read",)),
	PermissionDefinition("attachment.delete", "Supprimer une pièce jointe.", requires=("ticket.read",)),
	PermissionDefinition("attachment.read", "Télécharger une pièce jointe.", requires=("ticket.read",)),
	PermissionDefinition("audit.read", "Lire les entrées du journal d'audit."),
	PermissionDefinition("notification.read", "Lire ses propres notifications."),
	PermissionDefinition("analytics.read", "Lire les indicateurs et statistiques analytiques."),
	PermissionDefinition("analytics.read_any_application", "Consulter les analyses de toutes les applications (vue transverse).", requires=("analytics.read",)),
	PermissionDefinition("knowledge_base.read_recalculation", "Consulter la planification du recalcul complet du graphe de similarité."),
	PermissionDefinition("knowledge_base.manage_recalculation", "Modifier la planification du recalcul complet du graphe de similarité et le déclencher manuellement.", requires=("knowledge_base.read_recalculation",)),
	# A batch import creates tickets, so it presupposes the permission to create one.  This is
	# why the Admin role holds `ticket.create` despite an unstaffed administrator being unable
	# to submit the creation form: whether a *button* is worth offering is a question for the
	# surface that offers it, not a reason to withhold a permission another one depends on.
	PermissionDefinition("knowledge_base.batch_import", "Importer un fichier de tickets en masse et l'intégrer à la base de connaissances.", requires=("ticket.create",)),
	PermissionDefinition("knowledge_base.import_any_application", "Importer un fichier de tickets pour n'importe quelle application, au-delà de celle dont on a la charge.", requires=("knowledge_base.batch_import",)),
	# The umbrella "may this user reach the assistant at all" gate. No requires=: the assistant is
	# still meaningful with zero tools bound (a general chat interface with no data access), so
	# declaring a static prerequisite on any one underlying tool permission (ticket.read,
	# analytics.read, user.read) would be false, and declaring all of them would force every future
	# user of the assistant to hold every one of today's tool permissions -- defeating the point of
	# per-tool gating. Individual tools re-check their own existing permission independently at
	# bind time (conversational_assistant.application.tools.registry.build_available_tools).
	PermissionDefinition("conversational_assistant.use", "Utiliser l'assistant conversationnel."),
)

PERMISSIONS_BY_NAME = {permission.name: permission for permission in PERMISSION_CATALOG}
