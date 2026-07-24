from enum import StrEnum


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