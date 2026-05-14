"""Test bootstrap so `from database.scripts.X import Y` resolves.

The `database/scripts/` directory is a sibling of the installable `eleutheria-database`
package and is not on sys.path by default. Tests for the bootstrap/verification
helpers import directly from those scripts, so we add the repo root here.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
