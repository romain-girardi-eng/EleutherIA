#!/usr/bin/env python3
"""Wave D — Deduplication — 2026-05-16

Merge 4 duplicate node pairs flagged by the KG audit:

1. ``scholarly_work_inwood_1985_ethics_action`` (kept)
   ← ``pub_inwood_1985_ethics_human_action`` (dropped)
   Both = Brad Inwood, *Ethics and Human Action in Early Stoicism*
   (Oxford, Clarendon Press, 1985). The ``scholarly_work_`` entry carries
   the richer metadata (ISBN, topic_tags, author_id).

2. ``scholarly_work_long_1996_stoic_studies`` (kept, publisher = Cambridge UP)
   ← ``pub_long_1996_stoic_studies`` (dropped, publisher = California UP)
   A.A. Long, *Stoic Studies*, Cambridge University Press 1996 (the 2001
   California UP edition is a later paperback reissue, not the primary
   publisher). A publisher-correction audit trace is recorded on the kept
   node.

3. ``scholarly_argument_dihle_greek_philosophical_theology_v_0`` (kept, 2 edges)
   ← ``scholarly_argument_dihle_greek_vs_biblical_cosmology_an_4`` (dropped, 0 edges)
   Identical Dihle argument duplicated; keep more cited.

4. ``scholarly_argument_double_methodological_reframing_of_fr_1`` (kept,
   lex-smaller, 0 edges)
   ← ``scholarly_argument_double_taxonomy_of_free_will_position_1`` (dropped,
   0 edges)
   Identical Double trichotomy argument duplicated; both tied at 0 edges
   so the lexicographically smaller node_id wins.

For each merge:
- Both ``dropped`` and ``kept`` must exist (else ``already_merged++`` and skip).
- All edges referencing ``dropped`` in any of the 4 field forms
  (``source``, ``source_id``, ``target``, ``target_id``) are rewritten to
  point at ``kept``.
- Edges that become semantically identical (same kept-side endpoint, same
  relation, same other endpoint, same wave-metadata) after rewriting are
  de-duplicated.
- The ``dropped`` node is removed from ``data/kg/nodes.jsonl``.
- Idempotent: re-running on a clean graph reports all-zero counters.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

WAVE_TAG = "wave_d_deduplication_2026_05_16"
SNAPSHOT_DIR = ROOT / "data" / "kg" / "snapshots" / f"2026-05-16-pre-{WAVE_TAG}"

NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# Merge specs
# ---------------------------------------------------------------------------


MERGES: list[dict[str, Any]] = [
    {
        "kept": "scholarly_work_inwood_1985_ethics_action",
        "dropped": "pub_inwood_1985_ethics_human_action",
        "reason": (
            "Both nodes = Brad Inwood, Ethics and Human Action in Early Stoicism "
            "(Oxford: Clarendon Press, 1985). The scholarly_work_ entry has more "
            "complete metadata per audit §5."
        ),
    },
    {
        "kept": "scholarly_work_long_1996_stoic_studies",
        "dropped": "pub_long_1996_stoic_studies",
        "reason": (
            "A.A. Long, Stoic Studies, Cambridge University Press 1996 (later "
            "reissued California UP 2001 paperback). The pub_ entry incorrectly "
            "lists California UP as primary publisher; the scholarly_work_ entry "
            "correctly lists Cambridge UP. Keep CUP entry, drop California UP."
        ),
    },
    {
        # Dihle pair — kept resolved at runtime by edge count.
        "kept": None,
        "dropped": None,
        "candidates": [
            "scholarly_argument_dihle_greek_philosophical_theology_v_0",
            "scholarly_argument_dihle_greek_vs_biblical_cosmology_an_4",
        ],
        "reason": (
            "Same Dihle argument duplicated (identical label about Greek "
            "philosophical theology concentrated on order, regularity and "
            "beauty). Keep the more cited version (higher edge count) and drop "
            "the alias."
        ),
        "tag": "argument_dihle",
    },
    {
        "kept": None,
        "dropped": None,
        "candidates": [
            "scholarly_argument_double_methodological_reframing_of_fr_1",
            "scholarly_argument_double_taxonomy_of_free_will_position_1",
        ],
        "reason": (
            "Same Double trichotomy argument duplicated. Keep more cited; drop "
            "alias."
        ),
        "tag": "argument_double",
    },
]


LONG_PUBLISHER_CORRECTION_KEY = "publisher_correction_2026_05_16"
LONG_PUBLISHER_CORRECTION_VALUE = (
    "Audit 2026-05-16: duplicate pub_long_1996_stoic_studies (incorrectly "
    "listed California UP) was merged into this canonical entry; Long Stoic "
    "Studies = Cambridge UP 1996."
)
LONG_CANONICAL_PUBLISHER = "Cambridge University Press"
LONG_KEPT_ID = "scholarly_work_long_1996_stoic_studies"


# ---------------------------------------------------------------------------
# I/O helpers (mirror Wave B/C)
# ---------------------------------------------------------------------------


def load_nodes() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in NODES_PATH.read_text().splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def load_edges() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in EDGES_PATH.read_text().splitlines():
        if not line.strip():
            continue
        out.append(json.loads(line))
    return out


def write_nodes(nodes: list[dict[str, Any]]) -> None:
    with NODES_PATH.open("w") as fh:
        for n in nodes:
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")


def write_edges(edges: list[dict[str, Any]]) -> None:
    with EDGES_PATH.open("w") as fh:
        for e in edges:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


def parse_metadata(raw: Any) -> tuple[dict[str, Any], bool]:
    """Return ``(metadata-dict, was_string)``."""
    if raw is None:
        return {}, False
    if isinstance(raw, str):
        try:
            obj = json.loads(raw) if raw.strip() else {}
            if not isinstance(obj, dict):
                obj = {}
            return obj, True
        except json.JSONDecodeError:
            return {}, True
    if isinstance(raw, dict):
        return dict(raw), False
    return {}, False


def reencode_metadata(
    node_or_edge: dict[str, Any],
    md: dict[str, Any],
    was_string: bool,
) -> None:
    raw = node_or_edge.get("metadata")
    if was_string or isinstance(raw, str):
        node_or_edge["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node_or_edge["metadata"] = md


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} — skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Merge resolution
# ---------------------------------------------------------------------------


def count_edge_refs(edges: list[dict[str, Any]], node_ids: set[str]) -> dict[str, int]:
    counts: dict[str, int] = dict.fromkeys(node_ids, 0)
    for e in edges:
        for fld in ("source_id", "source", "target_id", "target"):
            v = e.get(fld)
            if isinstance(v, str) and v in counts:
                counts[v] += 1
    return counts


def resolve_unknown_kept(
    merges: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    node_ids_present: set[str],
) -> None:
    """Resolve any merge where ``kept``/``dropped`` are None using edge counts.

    Tie-breaker: lexicographically smaller node_id is kept.
    """
    for merge in merges:
        if merge.get("kept") and merge.get("dropped"):
            continue
        candidates = merge.get("candidates") or []
        if not candidates:
            continue

        present = [c for c in candidates if c in node_ids_present]
        if len(present) < 2:
            # One or both already absent; whichever is present (if any) is kept.
            if len(present) == 1:
                merge["kept"] = present[0]
                merge["dropped"] = next(c for c in candidates if c != present[0])
            else:
                # Both absent; just set arbitrary so loop skips with already_merged.
                merge["kept"] = candidates[0]
                merge["dropped"] = candidates[1]
            continue

        counts = count_edge_refs(edges, set(candidates))
        ranked = sorted(candidates, key=lambda c: (-counts[c], c))
        merge["kept"] = ranked[0]
        merge["dropped"] = ranked[1]


# ---------------------------------------------------------------------------
# Edge rerouting + deduplication
# ---------------------------------------------------------------------------


EDGE_ENDPOINT_FIELDS = ("source", "source_id", "target", "target_id")


def reroute_edges(
    edges: list[dict[str, Any]],
    rename_map: dict[str, str],
) -> int:
    """Rewrite all endpoint fields referencing a dropped id to the kept id.

    Returns the number of field-level mutations performed.
    """
    mutations = 0
    for e in edges:
        for fld in EDGE_ENDPOINT_FIELDS:
            val = e.get(fld)
            if isinstance(val, str) and val in rename_map:
                e[fld] = rename_map[val]
                mutations += 1
    return mutations


def edge_signature(e: dict[str, Any]) -> tuple[Any, ...]:
    """Stable signature used to detect duplicates after rerouting.

    We deliberately ignore ``edge_id``, ``created_at``, ``weight`` and
    ``metadata`` for the equality check — two edges with the same logical
    endpoints + relation collapse into one, keeping the first occurrence.
    """
    return (
        e.get("source_id") or e.get("source"),
        e.get("target_id") or e.get("target"),
        e.get("relation"),
    )


def dedup_edges(edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Drop edges that share signature with an earlier edge.

    Returns ``(unique_edges, num_dropped)``.
    """
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    dropped = 0
    for e in edges:
        sig = edge_signature(e)
        if sig in seen:
            dropped += 1
            continue
        seen.add(sig)
        out.append(e)
    return out, dropped


# ---------------------------------------------------------------------------
# Publisher correction (Long 1996)
# ---------------------------------------------------------------------------


def apply_long_publisher_correction(node: dict[str, Any]) -> bool:
    """Return True iff the node was mutated."""
    md, was_string = parse_metadata(node.get("metadata"))
    if md.get(LONG_PUBLISHER_CORRECTION_KEY):
        return False  # already corrected — idempotent
    current_publisher = md.get("publisher")
    needs_publisher_fix = current_publisher != LONG_CANONICAL_PUBLISHER
    if needs_publisher_fix:
        md["publisher"] = LONG_CANONICAL_PUBLISHER
    md[LONG_PUBLISHER_CORRECTION_KEY] = LONG_PUBLISHER_CORRECTION_VALUE
    md["audit_wave"] = WAVE_TAG
    reencode_metadata(node, md, was_string)
    node["updated_at"] = NOW_ISO
    return True


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-d] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    nodes_by_id = {node_id(n): n for n in nodes}
    node_ids_present = set(nodes_by_id.keys())

    resolve_unknown_kept(MERGES, edges, node_ids_present)

    rename_map: dict[str, str] = {}
    merges_applied = 0
    already_merged = 0
    argument_dihle_kept: str | None = None
    argument_double_kept: str | None = None

    for merge in MERGES:
        kept = merge["kept"]
        dropped = merge["dropped"]
        tag = merge.get("tag")

        kept_present = kept in node_ids_present
        dropped_present = dropped in node_ids_present

        if not dropped_present:
            already_merged += 1
            print(f"[skip] dropped={dropped} already absent (kept={kept})")
            if tag == "argument_dihle" and kept_present:
                argument_dihle_kept = kept
            if tag == "argument_double" and kept_present:
                argument_double_kept = kept
            continue

        if not kept_present:
            # Defensive: kept missing while dropped present — abort this merge.
            print(
                f"[warn] kept={kept} missing but dropped={dropped} present; "
                "skipping merge"
            )
            continue

        rename_map[dropped] = kept
        merges_applied += 1
        if tag == "argument_dihle":
            argument_dihle_kept = kept
        if tag == "argument_double":
            argument_double_kept = kept
        print(f"[merge] drop {dropped} → keep {kept}")

    edges_rerouted = reroute_edges(edges, rename_map) if rename_map else 0
    edges, edges_deduped = (
        dedup_edges(edges) if edges_rerouted else (edges, 0)
    )

    # Drop merged nodes
    if rename_map:
        nodes = [n for n in nodes if node_id(n) not in rename_map]

    # Publisher correction (idempotent on its own)
    publisher_correction_applied = False
    long_kept_node = next(
        (n for n in nodes if node_id(n) == LONG_KEPT_ID), None
    )
    if long_kept_node is not None:
        publisher_correction_applied = apply_long_publisher_correction(long_kept_node)

    if rename_map or publisher_correction_applied:
        write_nodes(nodes)
        write_edges(edges)
        print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")
    else:
        print("[write] no changes — skipping write")

    print(
        f"[wave-d] merges_applied={merges_applied}  "
        f"already_merged={already_merged}  "
        f"edges_rerouted={edges_rerouted}  edges_deduped={edges_deduped}"
    )
    print(
        f"[wave-d] argument_dihle_kept={argument_dihle_kept}  "
        f"argument_double_kept={argument_double_kept}"
    )
    print(f"[wave-d] publisher_correction_applied={publisher_correction_applied}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
