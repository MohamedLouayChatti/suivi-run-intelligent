from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttachmentContentDTO:
	filename: str
	content_type: str
	content: bytes
