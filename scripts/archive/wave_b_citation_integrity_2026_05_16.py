#!/usr/bin/env python3
"""Wave B — Citation Integrity P0 — 2026-05-16

Targeted, narrow wave (3 nodes mutated, 1 optional cascade rename):

- B1 : remove fabricated ``SC 227 (Junod, …)`` attribution from
       ``work_origen_de_oratione`` and ``work_origen_exhortation_martyrdom``.
       SC 227 in the Cerf catalog is Sozomène HE I-II (Bidez/Festugière/
       Grillet 1983), NOT Origen — there is no Sources Chrétiennes edition
       of either *Peri Euchēs* (De Oratione) or *Eis martyrion protreptikos*
       (Exhortatio). Replace with the correct GCS 2/3 Koetschau 1899
       critical reference and Bardy 1932 Cerf French translation.
- B2 : resolve the ``sc31_melito_peri_pascha_iv`` mislabeling. Disk
       inspection of the SC OCR file shows the text IS Méliton fr. IV as
       quoted by Eus. HE IV.26.3, preserved in SC 31 Bardy 1952
       (Eusèbe, HE Livres I-IV). The audit's claim that "SC 31 = HE V-VII"
       was itself wrong — SC 31 contains HE I-IV (SC 41 is HE V-VII).
       The node is therefore a legitimate Eusèbe HE IV.26 extract preserving
       a Méliton fragment, and the canonical ID should reflect that. Branch
       A: cascade-rename the three ``sc31_melito_peri_pascha_iv*`` nodes to
       ``passage_eusebius_he_iv_26_melito_fr_iv*`` and rewire all edges.
- B3 : reconcile the Justin SC 507 quotation variant on
       ``argument_justin_antifatalism``. The current description cites the
       Goodspeed/Otto reading ``τὸ ἐφ' ἡμῖν οὐδὲν ἔστιν ὅλως``; promote the
       SC 507 Munier 2006 critical reading ``οὐδὲ τὸ ἐφ' ἡμῖν ἐστιν ὅλως``
       to primary and record the variant in ``metadata.text_variants``.

The script is idempotent: re-running it on an already-fixed graph reports
all-zero counters and produces no diff.
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
SNAPSHOT_DIR = (
    ROOT / "data" / "kg" / "snapshots" / "2026-05-16-pre-wave_b_citation_integrity_2026_05_16"
)

WAVE_TAG = "wave_b_citation_integrity_2026_05_16"
NOW_ISO = datetime.now(UTC).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# B1 — fabricated SC 227 attribution removal
# ---------------------------------------------------------------------------

SC227_TARGETS: set[str] = {
    "work_origen_de_oratione",
    "work_origen_exhortation_martyrdom",
}

# Editions to append (replacing the fabricated SC 227 entry).
SC227_REPLACEMENT_EDITIONS: dict[str, list[str]] = {
    "work_origen_de_oratione": [
        "GCS 3 Koetschau 1899 (Origenes Werke II, critical edition)",
        "Bardy 1932 (Origène. La prière, French translation, Cerf)",
    ],
    "work_origen_exhortation_martyrdom": [
        "GCS 2 Koetschau 1899 (Origenes Werke I, critical edition)",
        "Bardy 1932 (Exhortation au martyre, French translation, Cerf)",
    ],
}

SC227_AUDIT_TRACE = (
    "Removed fabricated SC 227 (Junod) attribution per audit P0-1; "
    "SC 227 = Sozomène HE I-II (Bidez/Festugière/Grillet 1983), "
    "no SC edition exists for this Origen work."
)

SC227_AUDIT_TRACE_KEY = "hallucination_corrected_2026_05_16"


# ---------------------------------------------------------------------------
# B2 — sc31_melito_peri_pascha_iv cascade rename (Branch A)
# ---------------------------------------------------------------------------

# Disk evidence (verified 2026-05-16): the OCR file
# `02_Apologistes/bilingue/SC31_Melito_Sardensis_Fragments_IV_Sur_la_Pâque_livre_1_bilingue.txt`
# starts with `SC 31` header and cites `Eusèbe de Césarée, Histoire
# Ecclésiastique, IV, XXVI, 3 ; SC 31, 209 (Bardy).` — confirming that the
# text IS an Eus. HE IV.26.3 excerpt preserved in SC 31 (Bardy 1952, HE
# Livres I-IV). The audit's "SC 31 = HE V-VII" claim was itself a catalog
# error (SC 41 = HE V-VII; SC 31 = HE I-IV).
SC31_RENAME_MAP: dict[str, str] = {
    "sc31_melito_peri_pascha_iv": "passage_eusebius_he_iv_26_melito_fr_iv",
    "sc31_melito_peri_pascha_iv_chap3": "passage_eusebius_he_iv_26_melito_fr_iv_chap3",
    "sc31_melito_peri_pascha_iv_chap3_en": "passage_eusebius_he_iv_26_melito_fr_iv_chap3_en",
}

SC31_CANONICAL_SOURCE = (
    "Eus. HE IV.26.2-14 (Bardy SC 31, 1952) — preserves Méliton, "
    "Peri Pascha fr. IV (Hall 1979, OECT)"
)

SC31_DISK_EVIDENCE_PATH = (
    "[local-path] SHAL/02_Corpus/"
    "Sources chrétiennes txt/02_Apologistes/bilingue/"
    "SC31_Melito_Sardensis_Fragments_IV_Sur_la_Pâque_livre_1_bilingue.txt"
)

SC31_AUDIT_RESOLUTION = (
    "SC 31 prefix was a mislabeling: the text IS a real Eus. HE IV.26.3 "
    "excerpt preserved in SC 31 (Bardy 1952, HE Livres I-IV). Node renamed "
    "to make the canonical Eusèbe-HE provenance explicit. Children cascaded."
)


# ---------------------------------------------------------------------------
# B3 — Justin antifatalism quotation reconciliation
# ---------------------------------------------------------------------------

JUSTIN_NODE_ID = "argument_justin_antifatalism"

JUSTIN_VARIANT_GOODSPEED = "τὸ ἐφ' ἡμῖν οὐδὲν ἔστιν ὅλως"
JUSTIN_VARIANT_MUNIER = "οὐδὲ τὸ ἐφ' ἡμῖν ἐστιν ὅλως"

JUSTIN_TEXT_VARIANTS: list[dict[str, str]] = [
    {
        "reading": JUSTIN_VARIANT_MUNIER,
        "edition": "SC 507 Munier 2006 (critical)",
        "kind": "primary",
    },
    {
        "reading": JUSTIN_VARIANT_GOODSPEED,
        "edition": "Goodspeed 1914 / Otto 1876",
        "kind": "variant",
    },
]

JUSTIN_DESC_REPLACEMENT = (
    f"{JUSTIN_VARIANT_MUNIER} (SC 507 Munier 2006 ; var. Goodspeed 1914 : "
    f"{JUSTIN_VARIANT_GOODSPEED})"
)


# ---------------------------------------------------------------------------
# I/O helpers (mirror Wave A)
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


def reencode_metadata(node_or_edge: dict[str, Any], md: dict[str, Any], was_string: bool) -> None:
    raw = node_or_edge.get("metadata")
    if was_string or isinstance(raw, str):
        node_or_edge["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node_or_edge["metadata"] = md


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


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
# Task implementations
# ---------------------------------------------------------------------------


def _strip_sc227_from_value(value: Any) -> tuple[Any, bool]:
    """Return ``(cleaned_value, mutated)`` for either a list or string field."""
    if isinstance(value, list):
        cleaned_list: list[Any] = [
            x for x in value if not (isinstance(x, str) and "SC 227" in x)
        ]
        return cleaned_list, cleaned_list != value
    if isinstance(value, str):
        if "SC 227" not in value:
            return value, False
        cleaned_str: str = (
            value.replace("SC 227 (Junod, with French trans.)", "")
            .replace("SC 227 (Junod, critical text with French trans.)", "")
            .replace("SC 227 (Junod)", "")
            .replace("SC 227", "")
            .strip(" ,;")
        )
        return cleaned_str, cleaned_str != value
    return value, False


def apply_b1_sc227_removal(node: dict[str, Any]) -> bool:
    """Return True iff this node was mutated."""
    md, was_string = parse_metadata(node.get("metadata"))
    if md.get(SC227_AUDIT_TRACE_KEY):
        return False  # already fixed (idempotent)

    mutated = False
    for key in ("editions", "edition", "critical_edition"):
        if key not in md:
            continue
        new_val, changed = _strip_sc227_from_value(md[key])
        if changed:
            md[key] = new_val
            mutated = True

    # Append correct editions (de-duplicating against whatever survived)
    replacements = SC227_REPLACEMENT_EDITIONS[node_id(node)]
    if "editions" not in md or not isinstance(md.get("editions"), list):
        md["editions"] = []
    for edition in replacements:
        if edition not in md["editions"]:
            md["editions"].append(edition)
            mutated = True

    if mutated:
        md[SC227_AUDIT_TRACE_KEY] = SC227_AUDIT_TRACE
        md["audit_wave"] = WAVE_TAG
        reencode_metadata(node, md, was_string)
        node["updated_at"] = NOW_ISO
    return mutated


def apply_b2_sc31_rename(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> int:
    """Cascade-rename the 3 sc31_* nodes and rewire edges. Returns 1 if a
    rename happened, 0 if already done."""
    # Idempotency: if the parent's new ID already exists, skip entirely.
    new_parent = SC31_RENAME_MAP["sc31_melito_peri_pascha_iv"]
    by_id = {node_id(n): n for n in nodes}
    if new_parent in by_id:
        return 0
    if "sc31_melito_peri_pascha_iv" not in by_id:
        # Nothing to do; not applied and not present.
        return 0

    # Rename node IDs
    for old_id, new_id in SC31_RENAME_MAP.items():
        node = by_id.get(old_id)
        if node is None:
            continue
        node["node_id"] = new_id
        node["id"] = new_id

    # Update parent metadata with canonical_source + audit trace
    parent = by_id["sc31_melito_peri_pascha_iv"]  # same dict object, ID already mutated
    md, was_string = parse_metadata(parent.get("metadata"))
    md["canonical_source"] = SC31_CANONICAL_SOURCE
    md["audit_resolved_2026_05_16"] = SC31_AUDIT_RESOLUTION
    md["disk_evidence_path"] = SC31_DISK_EVIDENCE_PATH
    md["audit_wave"] = WAVE_TAG
    md["previous_node_id"] = "sc31_melito_peri_pascha_iv"
    # Also fix the nested `page_index[*].node_id` reference if it points to the old id.
    page_index = md.get("page_index")
    if isinstance(page_index, list):
        for entry in page_index:
            if (
                isinstance(entry, dict)
                and entry.get("node_id") == "sc31_melito_peri_pascha_iv_chap3"
            ):
                entry["node_id"] = SC31_RENAME_MAP["sc31_melito_peri_pascha_iv_chap3"]
    reencode_metadata(parent, md, was_string)
    parent["updated_at"] = NOW_ISO

    # Rewire edges
    for e in edges:
        for fld in ("source", "source_id", "target", "target_id"):
            val = e.get(fld)
            if isinstance(val, str) and val in SC31_RENAME_MAP:
                e[fld] = SC31_RENAME_MAP[val]

    return 1


def apply_b3_justin_variant(node: dict[str, Any]) -> bool:
    """Return True iff this node was mutated."""
    md, was_string = parse_metadata(node.get("metadata"))
    if md.get("primary_text_edition") == "SC 507 Munier 2006":
        return False  # already fixed

    md["primary_text_edition"] = "SC 507 Munier 2006"
    md["text_variants"] = JUSTIN_TEXT_VARIANTS
    md["audit_wave"] = WAVE_TAG

    desc = node.get("description") or ""
    if JUSTIN_VARIANT_GOODSPEED in desc and "Munier" not in desc:
        node["description"] = desc.replace(JUSTIN_VARIANT_GOODSPEED, JUSTIN_DESC_REPLACEMENT)

    reencode_metadata(node, md, was_string)
    node["updated_at"] = NOW_ISO
    return True


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-b] start :: wave={WAVE_TAG}")

    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    sc227_removed = 0
    justin_variant_recorded = 0
    sc31_updated = 0
    sc31_branch = "A"  # see B2 docstring; disk evidence supports Branch A.

    for n in nodes:
        nid = node_id(n)
        if nid in SC227_TARGETS and apply_b1_sc227_removal(n):
            sc227_removed += 1
        elif nid == JUSTIN_NODE_ID and apply_b3_justin_variant(n):
            justin_variant_recorded += 1

    sc31_updated = apply_b2_sc31_rename(nodes, edges)

    write_nodes(nodes)
    write_edges(edges)
    print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")

    print(
        f"[wave-b] sc227_removed={sc227_removed}  "
        f"sc31_branch={sc31_branch}  sc31_updated={sc31_updated}"
    )
    print(f"[wave-b] justin_variant_recorded={justin_variant_recorded}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
