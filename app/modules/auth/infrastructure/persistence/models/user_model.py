from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
    from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
    from app.modules.auth.infrastructure.persistence.models.application_assignment_model import ApplicationAssignmentModel

from app.shared.database.base import Base
from app.modules.auth.domain.enums.functional_team import FunctionalTeam

from .association_tables import role_permissions, user_direct_permissions, user_revoked_permissions


class UserModel(Base):
	__tablename__ = "users"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
	auth_provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
	email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
	# Two columns, no stored `display_name`: the full name is composed by the domain from
	# these, so a persisted copy would be a second answer free to drift from the first. Both
	# non-nullable but freely empty -- an identity provider does not require both halves, and
	# "" is the absence the composition rule already handles.
	first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
	last_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
	active: Mapped[bool] = mapped_column(Boolean, nullable=False)
	avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
	functional_team: Mapped[FunctionalTeam] = mapped_column(SAEnum(FunctionalTeam, name="auth_functional_team"), nullable=False)
	# A column rather than the user_roles join table this replaced: one role per user is a
	# domain invariant, and a schema that still said many-to-many would leave the database
	# free to hold a state the aggregate refuses to construct.
	role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True)

	# Loading is left to the queries that actually need the role object (the read repositories
	# spell it out with selectinload); the write path maps the aggregate from role_id alone and
	# would otherwise pay for a join it never reads.
	role: Mapped["RoleModel"] = relationship(back_populates="users", lazy="raise")
	direct_permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=user_direct_permissions, back_populates="direct_users", lazy="selectin"
	)
	revoked_permissions: Mapped[list["PermissionModel"]] = relationship(
		secondary=user_revoked_permissions, back_populates="revoked_users", lazy="selectin"
	)
	application_assignments: Mapped[list["ApplicationAssignmentModel"]] = relationship(
		back_populates="user", cascade="all, delete-orphan", lazy="selectin"
	)
