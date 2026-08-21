from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
    from app.modules.auth.infrastructure.persistence.models.user_model import UserModel

from app.shared.database.base import Base

from .association_tables import role_permissions


class RoleModel(Base):
	__tablename__ = "roles"
	__table_args__ = (Index("ix_roles_name", "name"),)

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
	# Reference data set by the roles seeder, not by anything at runtime -- server_default so the
	# column can be added NOT NULL to a table that already has rows.
	requires_primary_application: Mapped[bool] = mapped_column(
		Boolean, nullable=False, server_default="false", default=False
	)

	permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=role_permissions, back_populates="roles", lazy="selectin"
	)
	# Never read -- it exists only to give UserModel.role a back reference. Left un-loadable
	# on purpose: now that the link is a column on users, eager-loading this side would make
	# fetching one user pull in every other user sharing their role.
	#
	# passive_deletes="all" keeps `lazy="raise"` from turning a role deletion into an error about
	# lazy loading: SQLAlchemy neither loads nor rewrites the users on delete, so the seeder can
	# drop a role nobody holds, and dropping one people *do* hold fails as the foreign key
	# violation it actually is rather than by silently orphaning them.
	users: Mapped[list["UserModel"]] = relationship(
		back_populates="role", lazy="raise", passive_deletes="all"
	)
