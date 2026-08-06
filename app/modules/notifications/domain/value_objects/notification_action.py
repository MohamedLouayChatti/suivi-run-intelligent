from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from uuid import UUID


class NotificationAction(ABC):
	"""What the client should do when a notification is clicked.

	Deliberately not a URL: the backend stays independent of frontend routing.
	The frontend interprets each concrete action and decides where it leads.
	"""


@dataclass(frozen=True, slots=True)
class OpenTicketAction(NotificationAction):
	ticket_id: UUID


@dataclass(frozen=True, slots=True)
class OpenCommentAction(NotificationAction):
	ticket_id: UUID
	comment_id: UUID


@dataclass(frozen=True, slots=True)
class OpenUserAction(NotificationAction):
	user_id: UUID
