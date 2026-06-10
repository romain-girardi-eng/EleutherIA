"""Corpus tamper-evidence helpers (G14).

Canonical implementation of the passage checksum used by:

- ingest paths (``services/scaife.py``, ``scripts/ingest_scaife_work.py``,
  ``scripts/import_sc/importer.py``) to populate ``passages.text_sha256``;
- ``scripts/philological_audit/audit_text_drift.py`` to compare the live
  table against a baseline snapshot.

Hashing contract
----------------
``text_sha256(text)`` = SHA-256 hex digest of the **NFC-normalized** text,
UTF-8 encoded. NFC normalization means two byte-level encodings of the same
polytonic Greek (precomposed vs combining diacritics) hash identically,
while ANY change to the actual characters — including whitespace — changes
the digest. Nothing else is stripped or rewritten: the hash covers the text
as stored, modulo Unicode normalization form only.

These functions are pure (no DB access) except ``table_has_column``, a tiny
deploy-safety probe shared by the ingest scripts so they can populate
``text_sha256`` only after migration ``20260610_03_text_integrity.sql`` has
been applied.
"""

from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "DriftReport",
    "canonical_text_form",
    "compare_checksums",
    "table_has_column",
    "text_sha256",
]


def canonical_text_form(text: str) -> str:
    """Return the canonical (NFC) form of ``text`` used for hashing."""
    return unicodedata.normalize("NFC", text)


def text_sha256(text: str) -> str:
    """SHA-256 hex digest of the NFC-normalized, UTF-8 encoded text."""
    return hashlib.sha256(canonical_text_form(text).encode("utf-8")).hexdigest()


@dataclass
class DriftReport:
    """Result of comparing a checksum baseline against the current corpus.

    Keys are passage_ids; entry dicts carry at least ``sha256`` plus any
    reporting context (work, canonical_ref) recorded in the baseline.
    """

    added: dict[str, dict[str, Any]] = field(default_factory=dict)
    removed: dict[str, dict[str, Any]] = field(default_factory=dict)
    changed: dict[str, dict[str, Any]] = field(default_factory=dict)
    unchanged: int = 0

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary_counts(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "changed": len(self.changed),
            "unchanged": self.unchanged,
        }


def compare_checksums(
    baseline: Mapping[str, Mapping[str, Any]],
    current: Mapping[str, Mapping[str, Any]],
) -> DriftReport:
    """Compare two ``{passage_id: {"sha256": ..., ...}}`` maps.

    - ``added``   — passage_ids present now but absent from the baseline;
    - ``removed`` — passage_ids in the baseline that disappeared;
    - ``changed`` — passage_ids whose sha256 differs (entry includes both
      ``baseline_sha256`` and ``current_sha256``).

    Purely diagnostic — never mutates anything.
    """
    report = DriftReport()
    for pid, entry in current.items():
        base = baseline.get(pid)
        if base is None:
            report.added[pid] = dict(entry)
        elif base.get("sha256") != entry.get("sha256"):
            merged = dict(entry)
            merged["baseline_sha256"] = base.get("sha256")
            merged["current_sha256"] = entry.get("sha256")
            report.changed[pid] = merged
        else:
            report.unchanged += 1
    for pid, base in baseline.items():
        if pid not in current:
            report.removed[pid] = dict(base)
    return report


def table_has_column(cur: Any, table: str, column: str) -> bool:
    """True when ``column`` exists on ``table`` in the current schema.

    Works with any DB-API cursor (psycopg2). Used by ingest scripts so the
    ``text_sha256`` population is deploy-safe before the migration runs.
    """
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
        """,
        (table, column),
    )
    return cur.fetchone() is not None
