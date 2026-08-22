"""Deploy-critical scripts must stay parseable by the deploy container Python.

The production data deploy runs inside python:3.12-slim; PEP 758 bare
except-tuples (``except A, B:``) are 3.14-only syntax and have repeatedly
crept in (they parse fine in the 3.14 dev venv and in CI). This guard scans
every Python file the deploy container executes — plus their local imports —
for the pattern, so the break is caught before it reaches the host.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEPLOY_EXECUTED = [
    "database/scripts/bootstrap_supabase.py",
    "scripts/sync_corpus_to_db.py",
    "scripts/deploy_data_staged.py",
    # Shared modules imported by Python 3.12 ingestion/deploy/runtime paths.
    "backend/routes/works_extras.py",
    "graphrag/src/eleutheria_graphrag/agents/citability.py",
    "graphrag/src/eleutheria_graphrag/agents/dialectical_relations.py",
]

BARE_EXCEPT_TUPLE = re.compile(r"^\s*except\s+[A-Za-z_][\w.]*\s*,\s*[A-Za-z_]", re.M)


def test_no_314_only_except_syntax_in_deploy_scripts() -> None:
    offenders: list[str] = []
    for rel in DEPLOY_EXECUTED:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for m in BARE_EXCEPT_TUPLE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            offenders.append(f"{rel}:{line}")
    assert not offenders, (
        "PEP 758 bare except-tuple (3.14-only) in deploy-executed scripts; "
        f"the deploy container runs Python 3.12: {offenders}"
    )
