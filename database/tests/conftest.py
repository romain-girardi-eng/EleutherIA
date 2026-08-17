"""Test bootstrap so `from database.scripts.X import Y` resolves.

The `database/scripts/` directory is a sibling of the installable `eleutheria-database`
package and is not on sys.path by default. Tests for the bootstrap/verification
helpers import directly from those scripts, so we add the repo root here.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))

# pytest sets ``database/`` as its root when this package is tested directly,
# which can pre-import ``database/scripts`` under the ambiguous top-level name
# ``scripts``.  Clear only that wrong alias so repo-level deploy scripts remain
# importable in database tests.
_scripts = sys.modules.get("scripts")
if _scripts is not None:
    _scripts_file = Path(getattr(_scripts, "__file__", "")).resolve()
    if _scripts_file != _REPO_ROOT / "scripts" / "__init__.py":
        for _name in tuple(sys.modules):
            if _name == "scripts" or _name.startswith("scripts."):
                sys.modules.pop(_name, None)

# Pin the repo-level package before pytest later prepends ``database/`` to the
# import path for individual test modules.
importlib.import_module("scripts")
