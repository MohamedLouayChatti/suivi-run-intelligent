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
	leaving each layer to guess where in `"BEN AMOR Salma"` the surname ends."""
	email: str
	functional_team: FunctionalTeam
	role_name: str
	primary_application: Application
	backup_application: Application | None = None

	@property
	def display_name(self) -> str:
		return compose_display_name(self.first_name, self.last_name)


# The surname is written in capitals throughout, which is the convention of the ticket
# exports these were read from -- `BEN AMOR`, `MARTIN DUPONT` and `NASRI` are surnames of
# one, two and one word respectively, and `Sami Karim` is a given name of two. `Skander Ayari`
# and `Nour Karray` were the two entries recorded given-name-first and are split as such.
#
# Derived from the historical-tickets summary: functional team/role is the team with the
# highest ticket count for the user across applications (ties keep the first team seen);
# primary/backup application are the two applications with the highest ticket counts for
# the user (ties keep the first application seen), third and later applications ignored.
#
# Names are fictional -- these do not correspond to any real person or account.
HISTORICAL_USERS: tuple[HistoricalUserDefinition, ...] = (
	HistoricalUserDefinition(
		first_name="Sana",
		last_name="BOUZIDI",
		email="sana.bouzidi.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Yassine",
		last_name="KRAIEM",
		email="yassine.kraiem.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Wafa",
		last_name="MSADEK",
		email="wafa.msadek.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Karim",
		last_name="JELASSI",
		email="karim.jelassi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
		backup_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Salma",
		last_name="BEN AMOR",
		email="salma.benamor.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Dorra",
		last_name="HAMDI",
		email="dorra.hamdi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Sonia",
		last_name="TRABELSI",
		email="sonia.trabelsi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
		backup_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Walid",
		last_name="BEN YOUSSEF",
		email="walid.benyoussef.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.FCI,
	),
	HistoricalUserDefinition(
		first_name="Anis",
		last_name="GHARBI",
		email="anis.gharbi.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Léa",
		last_name="MARTIN DUPONT",
		email="lea.martindupont.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Fares",
		last_name="MEJRI",
		email="fares.mejri.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Emna",
		last_name="BOUAZIZ",
		email="emna.bouaziz.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Hend",
		last_name="CHAKROUN",
		email="hend.chakroun.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Rania",
		last_name="BEJI",
		email="rania.beji.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Amel",
		last_name="SOUISSI",
		email="amel.souissi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Olfa",
		last_name="BEN SALEM",
		email="olfa.bensalem.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Imen",
		last_name="JAOUADI",
		email="imen.jaouadi.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Sami Karim",
		last_name="NASRI",
		email="samikarim.nasri.test@gmail.com",
		functional_team=FunctionalTeam.CONFIGURATION,
		role_name="Ingénieur Support",
		primary_application=Application.COLORIS,
	),
	HistoricalUserDefinition(
		first_name="Skander",
		last_name="Ayari",
		email="ayari.skander.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
	HistoricalUserDefinition(
		first_name="Nour",
		last_name="Karray",
		email="karray.nour.test@gmail.com",
		functional_team=FunctionalTeam.SUPPORT,
		role_name="Ingénieur Support",
		primary_application=Application.VIO,
		backup_application=Application.AERO,
	),
)
