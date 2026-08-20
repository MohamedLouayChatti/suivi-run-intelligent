from __future__ import annotations

from app.modules.auth.domain.enums.application import Application

DEFAULT_ROLE_NAME = "Lecteur"
"""Role granted automatically to every newly created user."""

SUPPORT_ONLY_APPLICATIONS = frozenset({Application.AERO, Application.VIO})
"""Applications staffed by a single team, so their engineers are always Support.

Neither application has a Support/Configuration split at all -- Ticket Management's transfer
destinations already model both as one undivided destination, where FCI and COLORIS each get
one per team.  A Configuration engineer assigned to one of them, in any capacity, therefore
describes an organizational unit that does not exist, which is why the User aggregate refuses
it rather than leaving it to be noticed when the person cannot be given a single ticket.
"""
