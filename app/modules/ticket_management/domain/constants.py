from __future__ import annotations

from app.modules.ticket_management.domain.enums.application import Application

SUPPORT_ONLY_APPLICATIONS = frozenset({Application.AERO, Application.VIO})
"""Applications with no Support/Configuration split, so every one of their tickets is Support.

The same fact `TransferDestination` already encodes by giving AERO and VIO one destination
each where FCI and COLORIS get one per team: there is no Configuration queue to transfer to
because there is no Configuration team.  A ticket claiming otherwise names a queue nobody
staffs, and would be unassignable -- `ReassignTicketHandler` only accepts an assignee whose own
team matches the ticket's.
"""
