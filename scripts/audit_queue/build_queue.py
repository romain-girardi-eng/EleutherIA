#!/usr/bin/env python3
"""Build the unified integrity review queue from data/audit/ deferred findings.

Normalizes every deferred/pending audit finding (Greek fabrications, citation
fixes, anachronisms, mechanical scan findings) into ONE consolidated file,
data/audit/review_queue.jsonl, with a unified schema:

    {id, source_file, source_line, category, node_id, passage_id, summary,
     evidence, proposed_action, status, adjudicated_by, adjudicated_at,
     resolution, note}

Properties:
- Idempotent: ids are a stable hash of (source_file, source record content),
  and re-runs preserve adjudications already recorded in the existing queue.
  Content-derived ids mean an adjudication follows its finding even when a
  source file shrinks or reorders (e.g. a fixed deferred item is removed) —
  it can never silently migrate to whatever finding now sits on the old line.
- Read-only on sources: original audit files are never modified.
- No judgment: every new entry enters as status='pending'. Adjudication happens
  one item at a time via `eleutheria audit-queue adjudicate` — never in bulk.

Usage:
    python3 scripts/audit_queue/build_queue.py
    python3 scripts/audit_queue/build_queue.py --audit-dir data/audit --output data/audit/review_queue.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_DIR = PROJECT_ROOT / "data" / "audit"
DEFAULT_OUTPUT = DEFAULT_AUDIT_DIR / "review_queue.jsonl"

QUEUE_FILENAME = "review_queue.jsonl"

# Categories whose entries feed the integrity_status flagging SQL generator.
GREEK_CATEGORIES = frozenset({"greek_fabrication", "greek_unverified"})

# Wave-style deferred files carry a `dimension` key; map it to a queue category.
DIMENSION_CATEGORIES = {
    "J1_false_fact": "false_fact",
    "J2_greek": "greek_fabrication",
    "J3_biblio": "bibliographic",
    "J4_anachronism": "anachronism",
    "citation_descfix": "citation_fix",
}


def stable_id(source_file: str, record: dict[str, Any], occurrence: int = 0) -> str:
    """Content-derived id so adjudications track the finding, not its line.

    ``source_line`` is deliberately NOT part of the hash: deleting an earlier
    line from a deferred file must not re-key every later finding (which
    would re-attach human adjudications to the wrong finding). Byte-identical
    duplicate records in the same file are disambiguated by ``occurrence``.
    """
    fingerprint = json.dumps(record, ensure_ascii=False, sort_keys=True)
    key = f"{source_file}:{fingerprint}"
    if occurrence:
        key += f"#{occurrence}"
    digest = hashlib.sha1(key.encode()).hexdigest()
    return f"rq_{digest[:12]}"


def _truncate(text: str, limit: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _base_entry(
    source_file: str,
    source_line: int,
    category: str,
    *,
    node_id: str | None = None,
    passage_id: str | None = None,
    summary: str = "",
    evidence: dict[str, Any] | None = None,
    proposed_action: str | None = None,
) -> dict[str, Any]:
    return {
        # The id is content-derived from the raw source record; build_queue
        # assigns it after normalization (see stable_id).
        "id": None,
        "source_file": source_file,
        "source_line": source_line,
        "category": category,
        "node_id": node_id,
        "passage_id": passage_id,
        "summary": summary,
        "evidence": evidence or {},
        "proposed_action": proposed_action,
        "status": "pending",
        "adjudicated_by": None,
        "adjudicated_at": None,
        "resolution": None,
        "note": None,
    }


def _evidence_subset(rec: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    # Verbatim programmatic copy of source fields (incl. any Greek) — never retyped.
    return {k: rec[k] for k in keys if k in rec and rec[k] is not None}


def normalize_wave_deferred(
    rec: dict[str, Any], source_file: str, source_line: int
) -> dict[str, Any]:
    """wave1/wave3/cite_descfix deferred: dimension-tagged scholarly findings."""
    category = DIMENSION_CATEGORIES.get(rec.get("dimension", ""), "scholarly")
    summary = _truncate(
        rec.get("issue")
        or f"Deferred {rec.get('dimension', 'finding')} on field "
        f"{rec.get('field', '?')} ({rec.get('_defer', 'no defer reason')})"
    )
    return _base_entry(
        source_file,
        source_line,
        category,
        node_id=rec.get("node_id"),
        summary=summary,
        evidence=_evidence_subset(
            rec,
            (
                "dimension",
                "verdict",
                "severity",
                "fix_class",
                "field",
                "issue",
                "evidence",
                "current",
                "rationale",
                "sources",
                "final_confidence",
                "_defer",
            ),
        ),
        proposed_action=rec.get("proposed"),
    )


def normalize_cite_fix_deferred(
    rec: dict[str, Any], source_file: str, source_line: int
) -> dict[str, Any]:
    """cite_fix_deferred: repoint/remove passage-citation operations."""
    action = rec.get("action", "review")
    target = rec.get("new_passage_id")
    proposed = f"{action} citation {rec.get('bad_passage_id')}" + (
        f" -> {target}" if target else ""
    )
    return _base_entry(
        source_file,
        source_line,
        "citation_fix",
        node_id=rec.get("node_id"),
        passage_id=rec.get("bad_passage_id"),
        summary=_truncate(rec.get("rationale", proposed)),
        evidence=_evidence_subset(
            rec,
            (
                "action",
                "bad_passage_id",
                "new_passage_id",
                "confidence",
                "severity",
                "field",
                "current",
                "rationale",
                "_defer",
            ),
        ),
        proposed_action=proposed,
    )


def normalize_greek_insertions_deferred(
    rec: dict[str, Any], source_file: str, source_line: int
) -> dict[str, Any]:
    """greek_insertions_deferred: confirmed fabricated Greek, replacement deferred.

    Every record in this file documents a fabrication finding the auditor
    already confirmed; the `_defer` reason concerns verifying the *replacement*
    Greek against an edition, not the finding itself. We record
    verdict='confirmed' so the flagging SQL marks these nodes
    'fabrication_confirmed_pending_fix' rather than merely 'greek_unverified'.
    """
    evidence = _evidence_subset(
        rec, ("severity", "issue", "current", "sources", "rationale", "_defer")
    )
    evidence["verdict"] = "confirmed"
    return _base_entry(
        source_file,
        source_line,
        "greek_fabrication",
        node_id=rec.get("node_id"),
        summary=_truncate(rec.get("issue", "")),
        evidence=evidence,
        proposed_action=rec.get("proposed"),
    )


def normalize_greek_unmatched(
    rec: dict[str, Any], source_file: str, source_line: int
) -> dict[str, Any]:
    """greek_unmatched: Greek runs not matched to any corpus passage (unverified)."""
    n = rec.get("n_unmatched", "?")
    summary = _truncate(
        f"{n} Greek run(s) in '{rec.get('label', rec.get('node_id', ''))}' "
        f"unmatched against the corpus — verify against an edition or remove"
    )
    return _base_entry(
        source_file,
        source_line,
        "greek_unverified",
        node_id=rec.get("node_id"),
        summary=summary,
        evidence=_evidence_subset(
            rec, ("type", "label", "period", "n_runs", "n_unmatched", "unmatched_runs")
        ),
        proposed_action="verify each unmatched Greek run against a critical edition",
    )


def normalize_mechanical(
    rec: dict[str, Any], source_file: str, source_line: int
) -> dict[str, Any]:
    """mechanical_findings: scanner output (cts_urn_format, duplicates, etc.)."""
    ref_kind = rec.get("ref_kind")
    return _base_entry(
        source_file,
        source_line,
        "mechanical",
        node_id=rec.get("ref") if ref_kind == "node" else None,
        passage_id=rec.get("ref") if ref_kind == "passage" else None,
        summary=_truncate(f"[{rec.get('dim', 'mechanical')}] {rec.get('issue', '')}"),
        evidence=_evidence_subset(
            rec, ("dim", "severity", "fix_class", "ref_kind", "ref", "evidence")
        ),
        proposed_action=rec.get("proposed"),
    )


# (filename, normalizer) — pending/deferred findings only. Changelogs record
# already-applied fixes and strata.jsonl is a node inventory: neither is a
# pending finding, so neither enters the queue.
SOURCE_SPECS: tuple[
    tuple[str, Callable[[dict[str, Any], str, int], dict[str, Any]]], ...
] = (
    ("cite_descfix_deferred.jsonl", normalize_wave_deferred),
    ("cite_fix_deferred.jsonl", normalize_cite_fix_deferred),
    ("greek_insertions_deferred.jsonl", normalize_greek_insertions_deferred),
    ("greek_unmatched.jsonl", normalize_greek_unmatched),
    ("mechanical_findings.jsonl", normalize_mechanical),
    ("wave1_deferred.jsonl", normalize_wave_deferred),
    ("wave1_greek_deferred.jsonl", normalize_wave_deferred),
    ("wave2_anach_deferred.jsonl", normalize_wave_deferred),
    ("wave3_deferred.jsonl", normalize_wave_deferred),
)

ADJUDICATION_FIELDS = (
    "status",
    "adjudicated_by",
    "adjudicated_at",
    "resolution",
    "note",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")
    tmp.replace(path)


def build_queue(audit_dir: Path, output_path: Path) -> list[dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    if output_path.exists():
        existing = {e["id"]: e for e in read_jsonl(output_path)}

    entries: list[dict[str, Any]] = []
    occurrences: dict[str, int] = {}
    for filename, normalize in SOURCE_SPECS:
        path = audit_dir / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                entry = normalize(record, filename, lineno)
                base = stable_id(filename, record)
                entry["id"] = stable_id(filename, record, occurrences.get(base, 0))
                occurrences[base] = occurrences.get(base, 0) + 1
                prior = existing.get(entry["id"])
                if prior is not None:
                    # Re-runs must never clobber an adjudication. The id is
                    # content-derived, so a prior adjudication can only ever
                    # re-attach to the identical source record.
                    for field in ADJUDICATION_FIELDS:
                        entry[field] = prior.get(field, entry[field])
                entries.append(entry)

    write_jsonl(output_path, entries)
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    entries = build_queue(args.audit_dir, args.output)
    by_category: dict[str, int] = {}
    pending = 0
    for e in entries:
        by_category[e["category"]] = by_category.get(e["category"], 0) + 1
        if e["status"] == "pending":
            pending += 1
    print(f"review queue: {len(entries)} entries ({pending} pending) -> {args.output}")
    for category in sorted(by_category):
        print(f"  {category}: {by_category[category]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
