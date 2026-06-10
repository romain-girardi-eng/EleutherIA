"""Must-not-appear scanning against audit-derived forbidden strings.

The forbidden set lives in ``data/eval/must_not_appear.jsonl`` and is
machine-derived from the scholarly-audit queues by
``scripts/eval/build_gold_from_audit.py``. Each entry traces to its audit
source line; never edit the strings by hand.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MUST_NOT_APPEAR_PATH = REPO_ROOT / "data" / "eval" / "must_not_appear.jsonl"


@dataclass(frozen=True)
class ForbiddenString:
    string: str
    node_id: str
    status: str
    severity: str | None
    scan_kg: bool
    scan_answers: bool
    source_file: str
    source_line: int


def load_forbidden_strings(
    path: Path = MUST_NOT_APPEAR_PATH,
) -> list[ForbiddenString]:
    entries: list[ForbiddenString] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        entries.append(
            ForbiddenString(
                string=raw["string"],
                node_id=raw["node_id"],
                status=raw["status"],
                severity=raw.get("severity"),
                scan_kg=bool(raw.get("scan_kg")),
                scan_answers=bool(raw.get("scan_answers")),
                source_file=raw["source_file"],
                source_line=int(raw["source_line"]),
            )
        )
    return entries


def find_forbidden_strings(
    text: str, entries: list[ForbiddenString] | None = None
) -> list[ForbiddenString]:
    """Forbidden strings (answer-scannable set) found verbatim in ``text``."""
    if entries is None:
        entries = load_forbidden_strings()
    return [e for e in entries if e.scan_answers and e.string in text]


def assert_no_forbidden_strings(
    text: str, entries: list[ForbiddenString] | None = None
) -> None:
    """Raise ``AssertionError`` if ``text`` contains any audited fabrication."""
    hits = find_forbidden_strings(text, entries)
    if hits:
        details = "; ".join(
            f"{h.string!r} (audited at {h.source_file}:{h.source_line}, "
            f"node {h.node_id})"
            for h in hits
        )
        raise AssertionError(f"text contains audited fabricated strings: {details}")
