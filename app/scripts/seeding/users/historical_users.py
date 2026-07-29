from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.functional_team import FunctionalTeam


@dataclass(frozen=True, slots=True)
class HistoricalUserDefinition:
	"""A fake user reconstructed from the historical tickets dataset, used only so
	imported historical tickets can reference a valid assignee/author."""

	display_name: str
	email: str
	functional_team: FunctionalTeam
	role_name: str
	primary_application: Application
	backup_application: Application | None = None


# Derived from the historical-tickets summary: functional team/role is the team with the
# highest ticket count for the user across applications (ties keep the first team seen);
# primary/backup application are the two applications with the highest ticket counts for
# the user (ties keep the first application seen), third and later applications ignored.
HISTORICAL_USERS: tuple[HistoricalUserDefinition, ...] = (
	HistoricalUserDefinition(
		display_name="TERCHELLAH Rim",
		email="rim.terchellah.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="NAMOUCHI Ala",
		email="ala.namouchi.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="DAGHNOUJ Nesrine",
		email="nesrine.daghnouj.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		display_name="ZOUARI Wahbi",
		email="wahbi.zouari.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
		backup_application=Application.FCI,
	),
	HistoricalUserDefinition(
		display_name="BEN JEDDI Cyrine",
		email="cyrine.benjeddi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		display_name="SLITI Rihab",
		email="rihab.sliti.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		display_name="GHEBRICHE Marwa",
		email="marwa.ghebriche.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="BEN MBAREK Ahmed",
		email="ahmed.benmbarek.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		display_name="ZAKRAOUI Mohamed",
		email="mohamed.zakraoui.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="PIERROT CALLIZO Celia",
		email="celia.pierrotcallizo.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="GARA Kais",
		email="kais.gara.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="SAID Mariem",
		email="mariem.said.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="DHIFLAOUI Besma",
		email="besma.dhiflaoui.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="OUEASLATI Chiraz",
		email="chiraz.oueaslati.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="KCHAOU Amira",
		email="amira.kchaou.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="BEN TAHER Narjes",
		email="narjes.bentaher.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="FEZAI Fatma",
		email="fatma.fezai.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="BAFFOUN Mohamed Ali",
		email="mohamedali.baffoun.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Support Engineer",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		display_name="Akram Sahli",
		email="sahli.akram.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
	HistoricalUserDefinition(
		display_name="Mariem Hammami",
		email="hammami.mariem.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Support Engineer",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
)
