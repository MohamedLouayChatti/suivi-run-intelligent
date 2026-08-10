from __future__ import annotations

READ_ANY_APPLICATION_PERMISSION = "analytics.read_any_application"
"""Breadth permission: report across every application rather than one's own assignments.

Analytics keeps its own breadth permission rather than reusing Ticket Management's
`ticket.read_any_application`: aggregated, anonymised reporting over an application is a
weaker exposure than reading its individual tickets, so the two are worth granting
separately.  Holding this one is also what unlocks the cross-application overview.
"""
