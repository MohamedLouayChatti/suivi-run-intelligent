"""
Root-level conftest.

Its only job is to guarantee that the `app` package (containing the
ticket_management module under test) is importable, independent of the
current working directory pytest is invoked from. No fixtures live here;
module-specific fixtures live closer to the tests that need them.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))
