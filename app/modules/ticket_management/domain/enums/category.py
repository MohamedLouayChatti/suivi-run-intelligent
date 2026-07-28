from enum import StrEnum


class Category(StrEnum):
	CATEGORY_BUG = "Bug"
	CATEGORY_ANOMALIE_APPLICATIF = "Anomalie applicatif"
	CATEGORY_MANQUE_D_INFORMATION = "Manque d'information"
	CATEGORY_ASSISTANCE_CLIENT = "Assistance client"
	CATEGORY_BON_USAGE = "Bon usage"
	CATEGORY_VIDE = "vide"
	CATEGORY_SYNCHRONISATION_DES_DONNEES = "Synchronisation des données"
	CATEGORY_OPERATION_DE_SERVICE = "Opération de service"
	CATEGORY_HABILITATION = "Habilitation"
	CATEGORY_HORS_PERIMETRE = "Hors périmètre"
	CATEGORY_INFRASTRUCTURE = "Infrastructure"
