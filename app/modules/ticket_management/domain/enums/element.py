from enum import StrEnum


class Element(StrEnum):
	API = "API"
	CONNEXION_IMPOSSIBLE = "Connexion impossible"
	CUIVRE_IHM = "Cuivre IHM"
	DONNEES_ABSENTES = "Données absentes ou incorrectes"
	DROIT_HABILITATION = "Droit Habilitation"
	FIBRE_IHM_FTTE = "Fibre IHM FTTE"
	FIBRE_IHM_FTTH = "Fibre IHM FTTH"
	FIBRE_IHM_FTTO = "Fibre IHM FTTO"
	ERREUR = "Message d'erreur ou résultat inattendu"
	ORANGE_ELIGIBILTY_KO = "Orange-Eligibility KO"
	RETOUR_SUR_TICKET = "Retour sur ticket"
