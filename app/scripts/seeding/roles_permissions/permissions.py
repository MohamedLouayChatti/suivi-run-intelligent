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
	PermissionDefinition("user.read", "Read user information."),
	PermissionDefinition("user.activate", "Activate a user."),
	PermissionDefinition("user.deactivate", "Deactivate a user."),
	PermissionDefinition("role.read", "Read role information."),
	PermissionDefinition("role.assign", "Assign a role to a user."),
	PermissionDefinition("role.revoke", "Revoke a role from a user."),
	PermissionDefinition("permission.read", "Read permission information."),
	PermissionDefinition("permission.grant_to_role", "Grant a permission to a role."),
	PermissionDefinition("permission.revoke_from_role", "Revoke a permission from a role."),
	PermissionDefinition("permission.grant_to_user", "Grant a permission directly to a user."),
	PermissionDefinition("permission.revoke_from_user", "Revoke a direct permission from a user."),
	PermissionDefinition("ticket.create", "Create a ticket."),
	PermissionDefinition("ticket.read", "Read ticket information."),
	PermissionDefinition("ticket.assign", "Assign a ticket."),
	PermissionDefinition("ticket.change_priority", "Change a ticket priority."),
	PermissionDefinition("ticket.change_status", "Change a ticket status."),
	PermissionDefinition("ticket.transfer_application", "Transfer a ticket to another application."),
	PermissionDefinition("ticket.archive", "Archive a ticket."),
	PermissionDefinition("ticket.restore", "Restore an archived ticket."),
	PermissionDefinition("comment.create", "Add a comment to a ticket."),
	PermissionDefinition("comment.update", "Update a comment."),
	PermissionDefinition("comment.delete", "Delete a comment."),
	PermissionDefinition("attachment.create", "Add an attachment."),
	PermissionDefinition("attachment.delete", "Delete an attachment."),
)

PERMISSIONS_BY_NAME = {permission.name: permission for permission in PERMISSION_CATALOG}
