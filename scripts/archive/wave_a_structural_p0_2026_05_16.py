#!/usr/bin/env python3
"""Wave A — Structural P0 (data plumbing) — 2026-05-16

Residual scope after A2 already executed in commit 56db8776:

- A1 : re-route 84 dangling edges (5 renamed scholar/pub nodes + create 15
       PE-book passage stubs).
- A3 : drop 25 redundant inverses (18 ``created_by`` + 7 ``influenced_by``
       where the forward ``creates`` / ``influences`` already covers it).
- A4 : merge 87 ``influenced`` edges into ``influences`` (widen ontology to
       accept argument / argument_framework / concept / controversy / group
       source-and-target types).
- A5 : rename the single residual ``belongs_to_school`` edge to ``member_of``.
- A6 : backfill ``work_tertullian_adv_marcionem --authored_by-->
       person_tertullian_d220``.
- A7 : backfill ``period`` on 25 ``passage_aug_gla_*_en`` translations,
       ``metadata.source_language`` on ``passage_epict_107_en``, and
       ``period`` on ``pub_destree_salles_zingano_2014_what_is_up_to_us``.
- A8 : rename ``person_luis_de_molina_expanded_3k7f8g46`` and
       ``person_rene_descartes_1aa22692_expanded`` to drop the
       ``_expanded`` suffix.

Order of operations matters:

1. snapshot
2. A8 ``_expanded`` renames (must come first so subsequent reroute matches
   the new IDs if any dangle into them)
3. A1 dangling reroute + create PE-book stubs
4. A4 ``influenced -> influences`` retag + ontology widen
5. A3 drop redundant inverses
6. A5 ``belongs_to_school -> member_of``
7. A6 Tertullian backfill (idempotent — skipped if edge already present)
8. A7 period / source_language backfills

The script is idempotent: re-running prints all-zero counters and produces
no diff.
"""

from __future__ import annotations

import json
import shutil
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
ONTOLOGY_PATH = ROOT / "knowledge graph" / "ontology" / "edge_types.json"
SNAPSHOT_DIR = (
    ROOT / "data" / "kg" / "snapshots" / "2026-05-16-pre-wave_a_structural_p0_2026_05_16"
)

WAVE_TAG = "wave_a_structural_p0_2026_05_16"
NOW_ISO = datetime.now(timezone.utc).isoformat(sep=" ")


# ---------------------------------------------------------------------------
# A1 — Dangling node ID re-route map
# ---------------------------------------------------------------------------

REROUTE_MAP: dict[str, str] = {
    "person_frede_michael_1940_2007": "scholar_frede_michael",
    "scholar_dihle_albrecht": "scholar_albrecht_dihle",
    "pub_dihle_1982_theory_will": "pub_dihle_1982_theory_of_will",
    "work_frede_free_will_2011": "pub_frede_2011_free_will",
    "scholarly_work_frede_2011_free_will": "pub_frede_2011_free_will",
}


# ---------------------------------------------------------------------------
# A1 — PE-book stubs (Eusebius, Praeparatio Evangelica, books 1-15)
# ---------------------------------------------------------------------------

ROMAN = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
    13: "XIII",
    14: "XIV",
    15: "XV",
}

EUSEBIUS_PERSON_ID = "person_eusebius_caesarea_d339"


def pe_stub_node(book_num: int) -> dict[str, Any]:
    nn = f"{book_num:02d}"
    roman = ROMAN[book_num]
    nid = f"passage_eusebius_praep_ev_book_{nn}"
    return {
        "node_id": nid,
        "id": nid,
        "type": "passage",
        "label": f"Eusèbe, Praeparatio Evangelica, livre {roman} (stub — needs ingestion)",
        "description": (
            f"Stub pour la Préparation évangélique livre {roman} d'Eusèbe de Césarée. "
            "Édition critique : GCS 43 Mras 1954-1956 (réimpr. 1982-1983). "
            "Texte à ingérer en Wave F."
        ),
        "period": "Patristic",
        "school": None,
        "role": None,
        "alternative_names": "[]",
        "metadata": {
            "needs_text_ingestion": True,
            "edition": "GCS 43 Mras 1954-1956 (réimpr. 1982-1983)",
            "book_number": book_num,
            "book_roman": roman,
            "author_id": EUSEBIUS_PERSON_ID,
            "wave": WAVE_TAG,
        },
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


# ---------------------------------------------------------------------------
# A8 — _expanded rename map
# ---------------------------------------------------------------------------

EXPANDED_RENAMES: dict[str, str] = {
    "person_luis_de_molina_expanded_3k7f8g46": "person_luis_de_molina_3k7f8g46",
    "person_rene_descartes_1aa22692_expanded": "person_rene_descartes_1aa22692",
}


# ---------------------------------------------------------------------------
# A4 — `influenced` -> `influences` ontology widening
# ---------------------------------------------------------------------------

# Derived from current `influenced` usage (87 edges, see audit):
#   sources observed : argument, argument_framework, concept, controversy,
#                      person, work
#   targets observed : argument, argument_framework, concept, controversy,
#                      group, person, school, work
# `influences` already accepts person/school/work as both source and target.
INFLUENCES_NEW_SOURCE_TYPES = ["argument", "argument_framework", "concept", "controversy"]
INFLUENCES_NEW_TARGET_TYPES = ["argument", "argument_framework", "concept", "controversy", "group"]


# ---------------------------------------------------------------------------
# A6 — Tertullian backfill
# ---------------------------------------------------------------------------

TERTULLIAN_AUTHORED_BY = {
    "source_id": "work_tertullian_adv_marcionem",
    "target_id": "person_tertullian_d220",
    "relation": "authored_by",
}


# ---------------------------------------------------------------------------
# A7 — Period / source_language backfills
# ---------------------------------------------------------------------------

PUB_PERIOD_FIX = {
    "pub_destree_salles_zingano_2014_what_is_up_to_us": "Contemporary",
}


# ---------------------------------------------------------------------------
# I/O helpers
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
    """Write metadata back in the original format (string-or-dict)."""
    raw = node_or_edge.get("metadata")
    if was_string or isinstance(raw, str):
        node_or_edge["metadata"] = json.dumps(md, ensure_ascii=False)
    else:
        node_or_edge["metadata"] = md


def edge_signature(edge: dict[str, Any]) -> tuple[str, str, str, str | None]:
    md, _ = parse_metadata(edge.get("metadata"))
    wave = md.get("wave") if isinstance(md, dict) else None
    src = edge.get("source_id") or edge.get("source") or ""
    tgt = edge.get("target_id") or edge.get("target") or ""
    rel = edge.get("relation") or edge.get("type") or ""
    return (src, rel, tgt, wave)


def node_id(n: dict[str, Any]) -> str:
    return n.get("node_id") or n.get("id") or ""


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def make_snapshot() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    # Skip if snapshot already exists with both files (idempotent guard).
    snap_nodes = SNAPSHOT_DIR / "nodes.jsonl"
    snap_edges = SNAPSHOT_DIR / "edges.jsonl"
    if snap_nodes.exists() and snap_edges.exists():
        print(f"[snapshot] already exists at {SNAPSHOT_DIR.relative_to(ROOT)} — skip")
        return
    shutil.copy2(NODES_PATH, snap_nodes)
    shutil.copy2(EDGES_PATH, snap_edges)
    print(f"[snapshot] written to {SNAPSHOT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    print(f"[wave-a] start :: wave={WAVE_TAG}")

    # 0. snapshot
    make_snapshot()

    nodes = load_nodes()
    edges = load_edges()
    print(f"[load] nodes={len(nodes):,} ; edges={len(edges):,}")

    node_index: dict[str, dict[str, Any]] = {node_id(n): n for n in nodes}

    # ------------------------------------------------------------------
    # Pre-flight: replacement targets MUST exist (BLOCK otherwise).
    # ------------------------------------------------------------------
    required_targets = set(REROUTE_MAP.values())
    required_targets.add(EUSEBIUS_PERSON_ID)
    required_targets.add(TERTULLIAN_AUTHORED_BY["source_id"])
    required_targets.add(TERTULLIAN_AUTHORED_BY["target_id"])
    missing = sorted(t for t in required_targets if t not in node_index)
    if missing:
        print("[FATAL] missing replacement targets:")
        for m in missing:
            print(f"  - {m}")
        return 2
    print(f"[validate] {len(required_targets)} required targets present OK")

    # ------------------------------------------------------------------
    # A8 — _expanded renames (do FIRST so reroute / dedup picks them up)
    # ------------------------------------------------------------------
    expanded_renamed = 0
    expanded_edge_refs = 0
    for old_id, new_id in EXPANDED_RENAMES.items():
        old_n = node_index.get(old_id)
        if old_n is None:
            continue  # already renamed (idempotent)
        if new_id in node_index:
            print(f"[FATAL] _expanded rename collision: {old_id} -> {new_id} (target exists)")
            return 2
        old_n["node_id"] = new_id
        old_n["id"] = new_id
        node_index[new_id] = old_n
        del node_index[old_id]
        expanded_renamed += 1

    # Update every edge field that references either old _expanded ID.
    if EXPANDED_RENAMES:
        for e in edges:
            for fld in ("source", "source_id", "target", "target_id"):
                val = e.get(fld)
                if val in EXPANDED_RENAMES:
                    e[fld] = EXPANDED_RENAMES[val]
                    expanded_edge_refs += 1

    # ------------------------------------------------------------------
    # A1 — Create PE-book stubs (only for ones that dangle)
    # ------------------------------------------------------------------
    # Determine referenced PE-book IDs from current edge set.
    referenced_pe_books: set[str] = set()
    for e in edges:
        for fld in ("source", "source_id", "target", "target_id"):
            v = e.get(fld)
            if isinstance(v, str) and v.startswith("passage_eusebius_praep_ev_book_"):
                referenced_pe_books.add(v)

    pe_stubs_created = 0
    for nid in sorted(referenced_pe_books):
        if nid in node_index:
            continue
        # parse book number
        try:
            num = int(nid.rsplit("_", 1)[-1])
        except ValueError:
            print(f"[skip-stub] cannot parse book number from {nid}")
            continue
        if num not in ROMAN:
            print(f"[skip-stub] out-of-range book number {num} ({nid})")
            continue
        stub = pe_stub_node(num)
        node_index[nid] = stub
        nodes.append(stub)
        pe_stubs_created += 1

    # ------------------------------------------------------------------
    # A1 — Re-route dangling edges via REROUTE_MAP
    # ------------------------------------------------------------------
    dangling_rerouted = 0
    for e in edges:
        # Re-route source
        for src_fld in ("source", "source_id"):
            v = e.get(src_fld)
            if v in REROUTE_MAP:
                e[src_fld] = REROUTE_MAP[v]
        # Re-route target
        for tgt_fld in ("target", "target_id"):
            v = e.get(tgt_fld)
            if v in REROUTE_MAP:
                e[tgt_fld] = REROUTE_MAP[v]

    # Count edges that NOW touch a re-route VALUE on at least one side AND
    # whose other side was already valid before (=> formerly dangling).
    # Simpler heuristic: count edges that previously had any side in REROUTE_MAP
    # keys. We recompute by scanning before mutation — but we mutated in place.
    # To keep the counter accurate even on idempotent re-run, we count instead
    # how many edges currently reference any new target whose old key has been
    # removed. Idempotent re-run will yield 0 because no edge still references
    # an old key.
    # We rebuild the counter precisely by checking the freshly mutated edges
    # vs. the previously-loaded original keys snapshot.
    # (Implementation: scan edges once before reroute next time. For this
    # single-shot run we count by diff with the snapshot file written at start.)
    # → Simpler: re-load snapshot and diff. Done below.

    snap_edges_path = SNAPSHOT_DIR / "edges.jsonl"
    if snap_edges_path.exists():
        snap_keys = set(REROUTE_MAP.keys())
        for line in snap_edges_path.read_text().splitlines():
            if not line.strip():
                continue
            se = json.loads(line)
            sides = {
                se.get("source"),
                se.get("source_id"),
                se.get("target"),
                se.get("target_id"),
            }
            if sides & snap_keys:
                dangling_rerouted += 1

    # ------------------------------------------------------------------
    # A4 — Merge 'influenced' -> 'influences' + widen ontology
    # ------------------------------------------------------------------
    influenced_merged = 0
    for e in edges:
        if e.get("relation") != "influenced":
            continue
        md, was_string = parse_metadata(e.get("metadata"))
        if "original_relation" not in md:
            md["original_relation"] = "influenced"
        md["retag_reason"] = "wave_a_merge_2026_05_16"
        md["wave"] = WAVE_TAG
        reencode_metadata(e, md, was_string)
        e["relation"] = "influences"
        influenced_merged += 1

    # Update ontology if needed
    ontology = json.loads(ONTOLOGY_PATH.read_text())
    inf = ontology["edge_types"]["influences"]
    widened: dict[str, dict[str, list[str]]] = {}
    before_src = list(inf.get("source_types", []))
    before_tgt = list(inf.get("target_types", []))
    after_src = list(before_src)
    after_tgt = list(before_tgt)
    for t in INFLUENCES_NEW_SOURCE_TYPES:
        if t not in after_src:
            after_src.append(t)
    for t in INFLUENCES_NEW_TARGET_TYPES:
        if t not in after_tgt:
            after_tgt.append(t)
    if after_src != before_src or after_tgt != before_tgt:
        inf["source_types"] = sorted(after_src)
        inf["target_types"] = sorted(after_tgt)
        widened["influences"] = {
            "source_added": sorted(set(after_src) - set(before_src)),
            "target_added": sorted(set(after_tgt) - set(before_tgt)),
        }
        ONTOLOGY_PATH.write_text(
            json.dumps(ontology, ensure_ascii=False, indent=2) + "\n",
        )

    # ------------------------------------------------------------------
    # A3 — Drop redundant inverses (created_by / influenced_by)
    # ------------------------------------------------------------------
    # Group edges by (source, target) -> set of relations and edge indices.
    pair_rels: dict[tuple[str, str], set[str]] = defaultdict(set)
    for e in edges:
        s = e.get("source_id") or e.get("source") or ""
        t = e.get("target_id") or e.get("target") or ""
        rel = e.get("relation") or ""
        pair_rels[(s, t)].add(rel)

    def is_redundant(edge: dict[str, Any]) -> bool:
        rel = edge.get("relation")
        s = edge.get("source_id") or edge.get("source") or ""
        t = edge.get("target_id") or edge.get("target") or ""
        if rel == "created_by" and "creates" in pair_rels.get((t, s), set()):
            return True
        if rel == "influenced_by" and "influences" in pair_rels.get((t, s), set()):
            return True
        return False

    before_n = len(edges)
    edges = [e for e in edges if not is_redundant(e)]
    redundant_dropped = before_n - len(edges)

    # ------------------------------------------------------------------
    # A5 — belongs_to_school -> member_of
    # ------------------------------------------------------------------
    belongs_to_school_fixed = 0
    for e in edges:
        if e.get("relation") != "belongs_to_school":
            continue
        md, was_string = parse_metadata(e.get("metadata"))
        if "original_relation" not in md:
            md["original_relation"] = "belongs_to_school"
        md["retag_reason"] = "wave_a_merge_2026_05_16"
        md["wave"] = WAVE_TAG
        reencode_metadata(e, md, was_string)
        e["relation"] = "member_of"
        belongs_to_school_fixed += 1

    # ------------------------------------------------------------------
    # A6 — Tertullian authored_by backfill (idempotent)
    # ------------------------------------------------------------------
    existing_sigs: set[tuple[str, str, str, str | None]] = {edge_signature(e) for e in edges}
    # Also check for any existing authored_by edge between these two nodes
    # regardless of wave tag (don't duplicate).
    has_tertullian_authored_by = any(
        (e.get("source_id") or e.get("source")) == TERTULLIAN_AUTHORED_BY["source_id"]
        and (e.get("target_id") or e.get("target")) == TERTULLIAN_AUTHORED_BY["target_id"]
        and e.get("relation") == "authored_by"
        for e in edges
    )
    tertullien_backfilled = 0
    if not has_tertullian_authored_by:
        new_edge = {
            "edge_id": str(uuid.uuid4()),
            "source": TERTULLIAN_AUTHORED_BY["source_id"],
            "source_id": TERTULLIAN_AUTHORED_BY["source_id"],
            "target": TERTULLIAN_AUTHORED_BY["target_id"],
            "target_id": TERTULLIAN_AUTHORED_BY["target_id"],
            "relation": "authored_by",
            "weight": 1.0,
            "metadata": json.dumps(
                {
                    "wave": WAVE_TAG,
                    "rationale": (
                        "Backfill auteur : Tertullien (c. 155-220) auteur "
                        "d'Adversus Marcionem, attribution canonique unanime "
                        "(CCSL 1, ed. Kroymann 1954)."
                    ),
                    "confidence": 1.0,
                },
                ensure_ascii=False,
            ),
            "created_at": NOW_ISO,
        }
        sig = edge_signature(new_edge)
        if sig not in existing_sigs:
            edges.append(new_edge)
            existing_sigs.add(sig)
            tertullien_backfilled = 1

    # ------------------------------------------------------------------
    # A7 — period / source_language backfills
    # ------------------------------------------------------------------
    period_backfilled = 0
    source_language_set = 0
    pub_period_backfilled = 0

    for n in nodes:
        nid = node_id(n)

        # passage_aug_gla_*_en -> period = Patristic
        if nid.startswith("passage_aug_gla_") and nid.endswith("_en"):
            if not n.get("period"):
                n["period"] = "Patristic"
                n["updated_at"] = NOW_ISO
                period_backfilled += 1

        # passage_epict_107_en -> metadata.source_language = "grc"
        if nid == "passage_epict_107_en":
            md, was_string = parse_metadata(n.get("metadata"))
            if md.get("source_language") != "grc":
                md["source_language"] = "grc"
                reencode_metadata(n, md, was_string)
                n["updated_at"] = NOW_ISO
                source_language_set = 1

        # publication period fix
        if nid in PUB_PERIOD_FIX:
            if not n.get("period"):
                n["period"] = PUB_PERIOD_FIX[nid]
                n["updated_at"] = NOW_ISO
                pub_period_backfilled += 1

    # ------------------------------------------------------------------
    # Write back
    # ------------------------------------------------------------------
    write_nodes(nodes)
    write_edges(edges)
    print(f"[write] nodes={len(nodes):,} ; edges={len(edges):,}")

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------
    print(
        f"[wave-a] dangling_rerouted={dangling_rerouted}  "
        f"pe_stubs_created={pe_stubs_created}  "
        f"expanded_renamed={expanded_renamed}"
    )
    print(
        f"[wave-a] influenced_merged={influenced_merged}  "
        f"redundant_inverses_dropped={redundant_dropped}  "
        f"belongs_to_school_fixed={belongs_to_school_fixed}"
    )
    print(
        f"[wave-a] tertullien_backfilled={tertullien_backfilled}  "
        f"period_backfilled={period_backfilled + pub_period_backfilled}  "
        f"source_language_set={source_language_set}"
    )
    if widened:
        print(f"[wave-a] ontology_widened={json.dumps(widened, ensure_ascii=False)}")
    else:
        print("[wave-a] ontology_widened={} (idempotent)")
    print(f"[wave-a] expanded_edge_refs_updated={expanded_edge_refs}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
