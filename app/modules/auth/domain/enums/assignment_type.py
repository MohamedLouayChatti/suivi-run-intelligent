from enum import StrEnum


class AssignmentType(StrEnum):
	PRIMARY = "PRIMARY"
	BACKUP = "BACKUP"
	READ_ONLY = "READ_ONLY"
