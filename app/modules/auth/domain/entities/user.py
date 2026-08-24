from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.constants import SUPPORT_ONLY_APPLICATIONS
from app.modules.auth.domain.exceptions import (
	AuthorizationDomainError,
	BackupWithoutPrimaryApplication,
	DuplicateApplicationAssignment,
	FunctionalTeamNotAllowedForApplication,
	InvalidFunctionalTeam,
	InvalidPermissionState,
	InvalidRole,
	MultipleBackupApplications,
	MultiplePrimaryApplications,
)
from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


@dataclass
class User:
	"""Authorization aggregate that owns a user's role and permission exceptions."""

	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
	active: bool
	role_id: UUID
	"""The one role this user holds.

	Exactly one, never a set: a role is a named bundle of permissions, and letting a user
	carry several made "what may this person do" answerable only by unioning bundles nobody
	had designed to be combined.  Mandatory for the same reason -- a user with no role holds
	no permissions at all, which is not a state anything in the system wants to represent.
	Widening a single person's reach beyond their role is what the direct-permission
	exceptions below are for.
	"""
	avatar_url: str | None = None
	functional_team: FunctionalTeam = FunctionalTeam.SUPPORT
	application_assignments: set[ApplicationAssignment] = field(default_factory=set)
	direct_permission_ids: set[UUID] = field(default_factory=set)
	revoked_permission_ids: set[UUID] = field(default_factory=set)

	def __post_init__(self) -> None:
		if not isinstance(self.functional_team, FunctionalTeam):
			raise InvalidFunctionalTeam()
		if not isinstance(self.role_id, UUID):
			raise InvalidRole()
		if self.direct_permission_ids & self.revoked_permission_ids:
			raise InvalidPermissionState()
		self._validate_organizational_identity()

	def _validate_organizational_identity(self) -> None:
		self._validate_assignment_cardinality()
		self._validate_backup_requires_primary()
		self._validate_functional_team_against_assignments()

	def _validate_assignment_cardinality(self) -> None:
		"""A user runs at most one application and backs up at most one other.

		The set this is stored in only stops the identical (application, type) pair appearing
		twice, which was never the rule: two different PRIMARY applications, or the same
		application held as both PRIMARY and BACKUP, were both constructible and both describe
		staffing that does not exist. "At most" rather than "exactly": a user is created before
		anyone has assigned them anywhere, and having no application yet is an ordinary state.
		"""
		applications = [assignment.application for assignment in self.application_assignments]
		if len(applications) != len(set(applications)):
			raise DuplicateApplicationAssignment()

		types = [assignment.assignment_type for assignment in self.application_assignments]
		if types.count(AssignmentType.PRIMARY) > 1:
			raise MultiplePrimaryApplications()
		if types.count(AssignmentType.BACKUP) > 1:
			raise MultipleBackupApplications()

	def _validate_backup_requires_primary(self) -> None:
		"""Nobody backs up an application without running one of their own.

		A backup assignment is cover taken on *alongside* a project of one's own, never the
		whole of someone's remit -- so it presupposes a primary rather than standing in for
		one. Enforced here rather than in the schema because it is a rule about two rows
		together, which the partial unique indexes carrying the rest of the cardinality rule
		cannot express.
		"""
		if self.primary_application is not None:
			return
		if any(assignment.assignment_type == AssignmentType.BACKUP for assignment in self.application_assignments):
			raise BackupWithoutPrimaryApplication()

	@property
	def primary_application(self) -> Application | None:
		"""The one application this user runs, if they have been assigned one yet."""
		return next(
			(
				assignment.application
				for assignment in self.application_assignments
				if assignment.assignment_type == AssignmentType.PRIMARY
			),
			None,
		)

	def _validate_functional_team_against_assignments(self) -> None:
		"""AERO and VIO are staffed by Support alone, so nobody else may be assigned to them.

		Checked against every assignment rather than just the primary one: a backup covers the
		application for real, and a Configuration engineer covering AERO would be as unable to
		touch its tickets as one who owned it outright.
		"""
		if self.functional_team == FunctionalTeam.SUPPORT:
			return
		if any(assignment.application in SUPPORT_ONLY_APPLICATIONS for assignment in self.application_assignments):
			raise FunctionalTeamNotAllowedForApplication()

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		auth_provider_user_id: AuthProviderUserId,
		email: str,
		display_name: str,
		role_id: UUID,
		avatar_url: str | None = None,
		functional_team: FunctionalTeam = FunctionalTeam.SUPPORT,
		application_assignments: set[ApplicationAssignment] | None = None,
	) -> User:
		user = cls(
			id=id,
			auth_provider_user_id=auth_provider_user_id,
			email=email,
			display_name=display_name,
			active=False,
			role_id=role_id,
			avatar_url=avatar_url,
			functional_team=functional_team,
			application_assignments=set(application_assignments or ()),
		)
		return user

	def update_organizational_identity(
		self,
		*,
		functional_team: FunctionalTeam | None = None,
		application_assignments: set[ApplicationAssignment] | None = None,
	) -> None:
		previous_team = self.functional_team
		previous_assignments = self.application_assignments
		if functional_team is not None:
			self.functional_team = functional_team
		if application_assignments is not None:
			self.application_assignments = set(application_assignments)
		try:
			self._validate_organizational_identity()
		except AuthorizationDomainError:
			self.functional_team = previous_team
			self.application_assignments = previous_assignments
			raise

	def set_role(self, role_id: UUID) -> None:
		"""Replace the user's role, discarding every permission exception they carried.

		A role is a whole permission profile, not a starting point layered on: the exceptions
		below were decided against the *previous* role, so carrying them across would leave a
		user widened or narrowed for reasons nobody can reconstruct -- a direct grant made
		because the old role lacked something the new one includes, a revocation aimed at a
		permission the new role never had.  After this the user holds exactly what the new
		role holds, which is the only permission profile the change can be said to describe.

		It also removes the one way a role change could produce an incoherent effective set:
		a direct grant whose prerequisite came from the old role has nothing left to orphan.
		"""
		if not isinstance(role_id, UUID):
			raise InvalidRole()
		self.role_id = role_id
		self.direct_permission_ids = set()
		self.revoked_permission_ids = set()

	def grant_permission(self, permission_id: UUID) -> None:
		self.revoked_permission_ids.discard(permission_id)
		self.direct_permission_ids.add(permission_id)

	def revoke_permission(self, permission_id: UUID) -> None:
		self.direct_permission_ids.discard(permission_id)
		self.revoked_permission_ids.add(permission_id)

	def activate(self) -> None:
		if self.active:
			return
		self.active = True

	def deactivate(self) -> None:
		if not self.active:
			return
		self.active = False
