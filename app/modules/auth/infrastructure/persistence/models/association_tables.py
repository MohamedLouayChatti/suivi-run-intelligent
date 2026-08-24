from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.shared.database.base import Base


role_permissions = Table(
	"role_permissions",
	Base.metadata,
	Column("role_id", PGUUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
	Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)

user_direct_permissions = Table(
	"user_direct_permissions",
	Base.metadata,
	Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
	Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)

user_revoked_permissions = Table(
	"user_revoked_permissions",
	Base.metadata,
	Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
	Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)

permission_dependencies = Table(
	"permission_dependencies",
	Base.metadata,
	Column("permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
	Column("requires_permission_id", PGUUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
	CheckConstraint("permission_id <> requires_permission_id", name="ck_permission_dependencies_not_self"),
)
"""Which permissions each permission cannot be used without -- reference data, seeded.

Self-referential, and cascading on delete because a permission dropped from the catalog must
take its edges with it; `_remove_stale_permissions` would otherwise fail on the foreign key.
The check constraint rules out the one-node cycle; longer ones are the seeder's to refuse,
since no constraint expressible on a single row can see them.
"""
