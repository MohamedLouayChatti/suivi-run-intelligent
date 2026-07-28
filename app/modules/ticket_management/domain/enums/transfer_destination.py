from __future__ import annotations

from enum import StrEnum

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam


class TransferDestination(StrEnum):
	SUPPORT_FCI = "Support FCI"
	CONFIG_FCI = "Paramétrage FCI"
	SUPPORT_COLORIS = "Support COLORIS"
	CONFIG_COLORIS = "Paramétrage COLORIS"
	AERO = "AERO"
	VIO = "VIO"
	EEP = "EEP"
	CLIP = "CLIP"
	BANCO = "BANCO"
	ULYSSE = "Ulysse"
	ACACIA = "ACACIA"
	SANTAFE = "SantaFE"
	PROXIMA = "Proxima"
	HABILITATION = "Habilitation"
	DEVELOPMENT_TEAM = "Équipe Développement"

	def is_origin_of(self, functional_team: FunctionalTeam, application: Application) -> bool:
		"""True when this destination represents the ticket's own team/application, i.e. a no-op transfer."""
		origin = _ORIGIN_BY_DESTINATION.get(self)
		if origin is None:
			return False
		origin_team, origin_application = origin
		if origin_application != application:
			return False
		return origin_team is None or origin_team == functional_team


_ORIGIN_BY_DESTINATION: dict[TransferDestination, tuple[FunctionalTeam | None, Application]] = {
	TransferDestination.SUPPORT_FCI: (FunctionalTeam.SUPPORT, Application.FCI),
	TransferDestination.CONFIG_FCI: (FunctionalTeam.CONFIGURATION, Application.FCI),
	TransferDestination.SUPPORT_COLORIS: (FunctionalTeam.SUPPORT, Application.COLORIS),
	TransferDestination.CONFIG_COLORIS: (FunctionalTeam.CONFIGURATION, Application.COLORIS),
	# AERO and VIO have no support/config split: any ticket for that application is "home".
	TransferDestination.AERO: (None, Application.AERO),
	TransferDestination.VIO: (None, Application.VIO),
}