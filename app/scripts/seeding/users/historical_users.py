from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.person_name import compose_display_name


@dataclass(frozen=True, slots=True)
class HistoricalUserDefinition:
	"""A fake user reconstructed from the historical tickets dataset, used only so
	imported historical tickets can reference a valid assignee/author."""

	first_name: str
	last_name: str
	"""The two halves of the name, held apart for the same reason the aggregate holds them
	apart: the full name is composed from these, so the catalog states the split rather than
	leaving each layer to guess where in `"BEN JEDDI Cyrine"` the surname ends."""
	email: str
	functional_team: FunctionalTeam
	role_name: str
	primary_application: Application
	backup_application: Application | None = None

	@property
	def display_name(self) -> str:
		return compose_display_name(self.first_name, self.last_name)


# The surname is written in capitals throughout, which is the convention of the ticket
# exports these were read from -- `BEN JEDDI`, `PIERROT CALLIZO` and `BAFFOUN` are surnames of
# one, two and one word respectively, and `Mohamed Ali` is a given name of two. `Akram Sahli`
# and `Mariem Hammami` were the two entries recorded given-name-first and are split as such.
#
# Derived from the historical-tickets summary: functional team/role is the team with the
# highest ticket count for the user across applications (ties keep the first team seen);
# primary/backup application are the two applications with the highest ticket counts for
# the user (ties keep the first application seen), third and later applications ignored.
HISTORICAL_USERS: tuple[HistoricalUserDefinition, ...] = (
	HistoricalUserDefinition(
		first_name="Rim",
		last_name="TERCHELLAH",
		email="rim.terchellah.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Ala",
		last_name="NAMOUCHI",
		email="ala.namouchi.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Nesrine",
		last_name="DAGHNOUJ",
		email="nesrine.daghnouj.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Wahbi",
		last_name="ZOUARI",
		email="wahbi.zouari.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
		backup_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Cyrine",
		last_name="BEN JEDDI",
		email="cyrine.benjeddi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Rihab",
		last_name="SLITI",
		email="rihab.sliti.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Marwa",
		last_name="GHEBRICHE",
		email="marwa.ghebriche.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Ahmed",
		last_name="BEN MBAREK",
		email="ahmed.benmbarek.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Mohamed",
		last_name="ZAKRAOUI",
		email="mohamed.zakraoui.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Celia",
		last_name="PIERROT CALLIZO",
		email="celia.pierrotcallizo.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Kais",
		last_name="GARA",
		email="kais.gara.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Mariem",
		last_name="SAID",
		email="mariem.said.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Besma",
		last_name="DHIFLAOUI",
		email="besma.dhiflaoui.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Chiraz",
		last_name="OUEASLATI",
		email="chiraz.oueaslati.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Amira",
		last_name="KCHAOU",
		email="amira.kchaou.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Narjes",
		last_name="BEN TAHER",
		email="narjes.bentaher.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Fatma",
		last_name="FEZAI",
		email="fatma.fezai.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Mohamed Ali",
		last_name="BAFFOUN",
		email="mohamedali.baffoun.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Akram",
		last_name="Sahli",
		email="sahli.akram.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
	HistoricalUserDefinition(
		first_name="Mariem",
		last_name="Hammami",
		email="hammami.mariem.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
)
