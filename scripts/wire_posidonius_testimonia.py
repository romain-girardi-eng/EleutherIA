#!/usr/bin/env python3
"""Wire existing KG passages mentioning Posidonius to the canonical person node.

Context
-------
Posidonius of Apamea (c. 135-51 BCE), the major Middle Stoa figure, left no
extant writings. The Edelstein-Kidd 1972 critical edition is under copyright
and cannot be ingested. The pragmatic alternative is to *wire* every existing
KG passage that mentions Posidonius -- mostly Cicero (De Fato, De Divinatione),
Seneca (Epistulae Morales), Augustine (De Civitate Dei), Diogenes Laertius
VII.149-157, Galen (DPP) -- to the canonical ``person_posidonius_apameia_135_51bce``
node via ``discusses`` edges. This produces *testimonia*-level provenance
evidence for the DHQ article without ingesting new copyright-protected text.

Pattern
-------
Each edge carries metadata flagging the wiring provenance::

    {
        "relation_type": "testimonium",
        "auto_wired": true,
        "wired_from_keyword_match": true,
        "wired_date": "2026-05-16"
    }

Idempotent
----------
Reruns are safe: the script reads ``data/kg/edges.jsonl``, computes the set of
existing ``(source_id, "discusses", target_id)`` triples, and only emits edges
that are not already present. Dry-run by default; pass ``--commit`` to write.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

POSIDONIUS_PERSON_ID = "person_posidonius_apameia_135_51bce"
WIRED_DATE = "2026-05-16"

# Keyword variants to match in passage text. ``posidoni`` covers Latin
# ``Posidonius``/``Posidonio``/``Posidonii`` and Greek transliterations.
_KEYWORDS = ("posidoni",)


def find_posidonius_passages() -> list[str]:
    """Return passage node IDs whose description mentions Posidonius."""
    if not NODES_PATH.exists():
        return []
    out: list[str] = []
    with NODES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            node = json.loads(raw)
            if node.get("type") != "passage":
                continue
            text = (
                (node.get("description") or "")
                + " "
                + (node.get("description_en") or "")
            ).lower()
            if any(kw in text for kw in _KEYWORDS):
                out.append(node["id"])
    return out


def build_discusses_edge(source_id: str) -> dict:
    """Build a ``discusses`` edge from a passage to the Posidonius person node.

    Metadata is stored as a JSON string to match the existing convention
    observed in ``data/kg/edges.jsonl`` (other ``discusses`` edges serialize
    their metadata field as a string).
    """
    metadata = {
        "relation_type": "testimonium",
        "auto_wired": True,
        "wired_from_keyword_match": True,
        "wired_date": WIRED_DATE,
    }
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "edge_id": str(uuid.uuid4()),
        "metadata": json.dumps(metadata, ensure_ascii=False),
        "relation": "discusses",
        "source": source_id,
        "source_id": source_id,
        "target": POSIDONIUS_PERSON_ID,
        "target_id": POSIDONIUS_PERSON_ID,
        "weight": 1.0,
    }


def _existing_discusses_triples() -> set[tuple[str, str]]:
    """Return ``{(source_id, target_id)}`` for all existing ``discusses`` edges."""
    triples: set[tuple[str, str]] = set()
    if not EDGES_PATH.exists():
        return triples
    with EDGES_PATH.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            e = json.loads(raw)
            if e.get("relation") != "discusses":
                continue
            src = e.get("source_id") or e.get("source")
            tgt = e.get("target_id") or e.get("target")
            if src and tgt:
                triples.add((src, tgt))
    return triples


def plan_new_edges() -> tuple[list[dict], list[str]]:
    """Compute the new edges to append plus the list of already-wired passages.

    Returns ``(new_edges, already_wired)``.
    """
    passages = find_posidonius_passages()
    existing = _existing_discusses_triples()
    new_edges: list[dict] = []
    already: list[str] = []
    for pid in passages:
        if (pid, POSIDONIUS_PERSON_ID) in existing:
            already.append(pid)
            continue
        new_edges.append(build_discusses_edge(pid))
    return new_edges, already


def _append_edges(edges: list[dict]) -> None:
    with EDGES_PATH.open("a", encoding="utf-8") as fh:
        for edge in edges:
            fh.write(json.dumps(edge, ensure_ascii=False))
            fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Write new edges to data/kg/edges.jsonl (default: dry-run).",
    )
    args = parser.parse_args(argv)

    passages = find_posidonius_passages()
    new_edges, already = plan_new_edges()

    print(f"Passages mentioning Posidonius: {len(passages)}")
    print(f"  Already wired (discusses → {POSIDONIUS_PERSON_ID}): {len(already)}")
    print(f"  New edges to add: {len(new_edges)}")

    if new_edges:
        sample = new_edges[: min(5, len(new_edges))]
        print("\nSample new edges:")
        for edge in sample:
            print(f"  {edge['source_id']}  --discusses-->  {edge['target_id']}")

    if not args.commit:
        print("\n[dry-run] No changes written. Pass --commit to persist.")
        return 0

    if not new_edges:
        print("\nNothing to commit. Exiting.")
        return 0

    _append_edges(new_edges)
    print(f"\nAppended {len(new_edges)} edges to {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
