#!/usr/bin/env python3
"""Semantically re-ground mis-bound Cicero passage-nodes to genuine loci.

Background
----------
100 KG nodes ``passage_cic_div_*`` and 22 nodes ``passage_cic_nat_deor_*``
(type=passage) were created from the WRONG corpus slots: their stored text is
Cicero *Topica* (phi042) / *Orator* (phi041) prose, and the trailing "N" in the
label ("De Div. N" / "De Nat. Deor. N") is merely the Topica/Orator section
index — NOT a genuine *De Divinatione* / *De Natura Deorum* locus. Their
``passage_citations`` rows therefore point at Topica/Orator passages.

The genuine works are now correctly ingested:
  - De Divinatione   urn_cts_latinlit_phi0474_phi053_lat  (refs 1.1 .. 2.150)
  - De Natura Deorum urn_cts_latinlit_phi0474_phi050_lat  (refs 1.1 .. 3.95)

Recovery strategy (SEMANTIC, not mechanical — ZERO fabrication)
---------------------------------------------------------------
The fake N is noise, and the node's own stored text (Topica/Orator) is useless
for matching. The only signal is the KG *argument* that cites the passage-node:
its label/description states what Cicero passage it is about, often with an
explicit locus. We re-ground a node ONLY when:

  (a) the node is cited by exactly one argument (no conflicting target loci),
      AND
  (b) that argument names a single, explicit Cicero locus (e.g. "De div. II,
      8, 21"), AND
  (c) the genuine passage at that locus, read verbatim from the corpus,
      contains the exact doctrine/phrase the argument quotes.

Each accepted re-grounding is hard-coded below (CONFIDENT_MATCHES) after manual
verification of the genuine passage text against the argument's claim. Nothing
is matched by heuristic. Anything not in CONFIDENT_MATCHES is left untouched and
written to data/corpus/REVIEW_cicero_unrecovered.md for manual resolution.

For an accepted match this script:
  1. re-points the node's ``passage_citations`` row(s) to the genuine passage,
  2. corrects the KG node's ``description`` (stored text), ``label``,
     ``cts_urn`` (in metadata) so it stops carrying Topica/Orator text,
  3. records confidence and provenance in the node metadata.

Dry-run by default; --commit to mutate the DB. A pre-mutation snapshot of every
touched citation + node is written under
data/corpus/fix_snapshots/rehome_cicero_semantic_2026_05_25/.

Usage:
    .venv/bin/python -m scripts.rehome_cicero_semantic_2026_05_25 [--commit]

Dependencies: asyncpg (DATABASE_URL from .env), lxml not required here.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "data" / "corpus" / "fix_snapshots" / "rehome_cicero_semantic_2026_05_25"
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
REVIEW_PATH = ROOT / "data" / "corpus" / "REVIEW_cicero_unrecovered.md"

DIV_CANONICAL = "urn_cts_latinlit_phi0474_phi053_lat"      # De Divinatione (genuine)
NATDEOR_CANONICAL = "urn_cts_latinlit_phi0474_phi050_lat"  # De Natura Deorum (genuine)

CITES_RELATIONS = ("cites_primary_source", "evidenced_by")

# ---------------------------------------------------------------------------
# CONFIDENT, MANUALLY-VERIFIED SEMANTIC MATCHES.
#
# Each entry: node_id -> (genuine_work_canonical, genuine_canonical_ref, reason).
# Only nodes whose sole citing argument names ONE explicit locus AND whose
# genuine passage text was read and confirmed to contain the quoted doctrine.
# ---------------------------------------------------------------------------
CONFIDENT_MATCHES: dict[str, tuple[str, str, str]] = {
    # Cited solely by argument_cicero_de_div_anti_mantike_amand1945, whose label
    # is literally "De divinatione II, 8, 21" and which quotes the pragmatic
    # anti-divination dilemma. Genuine De Div 2.21 contains it verbatim:
    #   "Ubi est igitur ista divinatio Stoicorum? quae, si fato omnia fiunt,
    #    nihil nos admonere potest, ut cautiores simus ... sin autem id potest
    #    flecti, nullum est fatum; ita ne divinatio quidem, quoniam ea rerum
    #    futurarum est."
    "passage_cic_div_21": (
        DIV_CANONICAL,
        "2.21",
        "Sole citing argument (argument_cicero_de_div_anti_mantike_amand1945) names "
        "the explicit locus 'De divinatione II, 8, 21' and quotes the Stoic-divination "
        "dilemma; genuine De Div 2.21 contains it verbatim ('Ubi est igitur ista "
        "divinatio Stoicorum? ... sin autem id potest flecti, nullum est fatum').",
    ),
}


def _db_url() -> str:
    for line in (ROOT / ".env").open(encoding="utf-8"):
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL not found in .env")


def _pg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgres://" + url[len("postgresql://"):]
    return url


def _node_id(obj: dict) -> str:
    return obj.get("id") or obj.get("node_id") or ""


def _load_kg_nodes(predicate) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with NODES_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            nid = _node_id(obj)
            if nid and predicate(nid):
                out[nid] = obj
    return out


def _load_node_to_args() -> dict[str, list[str]]:
    """Map each cic_div/cic_nat_deor passage-node -> list of citing argument ids."""
    node2args: dict[str, list[str]] = defaultdict(list)
    with EDGES_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            tgt = e.get("target") or e.get("target_id") or ""
            src = e.get("source") or e.get("source_id") or ""
            if e.get("relation") in CITES_RELATIONS and (
                tgt.startswith("passage_cic_div_") or tgt.startswith("passage_cic_nat_deor_")
            ):
                node2args[tgt].append(src)
    return node2args


def _load_arg_descriptions(arg_ids: set[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with NODES_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            nid = _node_id(obj)
            if nid in arg_ids:
                out[nid] = {
                    "label": obj.get("label") or "",
                    "description": obj.get("description") or "",
                }
    return out


async def _genuine_passage(conn: asyncpg.Connection, canonical_id: str, ref: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT p.passage_id::text AS passage_id, p.cts_urn, p.canonical_ref, p.text_content
        FROM free_will.passages p
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE w.canonical_id = $1 AND p.canonical_ref = $2
        """,
        canonical_id,
        ref,
    )
    return dict(row) if row else None


async def _node_citations(conn: asyncpg.Connection, node_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT pc.citation_id::text AS citation_id, pc.passage_id::text AS passage_id,
               pc.kg_node_id, pc.citation_type, pc.confidence,
               p.canonical_ref AS old_ref, p.cts_urn AS old_cts_urn,
               w.canonical_id  AS old_work
        FROM free_will.passage_citations pc
        JOIN free_will.passages p ON p.passage_id = pc.passage_id
        JOIN free_will.ancient_works w ON w.work_id = p.work_id
        WHERE pc.kg_node_id = $1
        """,
        node_id,
    )
    return [dict(r) for r in rows]


async def _node_row(conn: asyncpg.Connection, node_id: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT node_id, id, label, description, metadata FROM free_will.kg_nodes WHERE node_id = $1",
        node_id,
    )
    return dict(row) if row else None


def _parse_metadata(meta_raw: Any) -> dict:
    if isinstance(meta_raw, dict):
        return dict(meta_raw)
    if isinstance(meta_raw, str) and meta_raw.strip():
        try:
            parsed = json.loads(meta_raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


async def main(commit: bool) -> int:
    import asyncpg

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).isoformat()
    print(f"Mode: {'COMMIT' if commit else 'DRY-RUN'}")
    print(f"Timestamp: {ts}")

    node2args = _load_node_to_args()
    all_cic_nodes = _load_kg_nodes(
        lambda n: n.startswith("passage_cic_div_") or n.startswith("passage_cic_nat_deor_")
    )
    print(f"cic_div + cic_nat_deor passage-nodes loaded: {len(all_cic_nodes)}")
    print(f"  cited by >=1 argument: {len(node2args)}")
    print(f"  confident semantic matches declared: {len(CONFIDENT_MATCHES)}")

    arg_ids = {a for args in node2args.values() for a in args}
    arg_desc = _load_arg_descriptions(arg_ids)

    conn: asyncpg.Connection = await asyncio.wait_for(
        asyncpg.connect(_pg_url(_db_url())), timeout=30
    )
    try:
        # --- Build & verify the re-grounding plan -------------------------
        plan: list[dict] = []
        for node_id, (work_canon, ref, reason) in CONFIDENT_MATCHES.items():
            if node_id not in all_cic_nodes:
                raise SystemExit(f"Declared match references unknown node {node_id!r}")
            citing = node2args.get(node_id, [])
            if len(citing) != 1:
                raise SystemExit(
                    f"Refusing to re-ground {node_id}: cited by {len(citing)} arguments "
                    f"(expected exactly 1 for a confident match): {citing}"
                )
            genuine = await _genuine_passage(conn, work_canon, ref)
            if not genuine:
                raise SystemExit(
                    f"Genuine passage {work_canon} {ref} not found — cannot re-ground {node_id}"
                )
            cits = await _node_citations(conn, node_id)
            node = await _node_row(conn, node_id)
            if node is None:
                raise SystemExit(f"KG node {node_id} not present in kg_nodes")
            plan.append(
                {
                    "node_id": node_id,
                    "citing_argument": citing[0],
                    "genuine_passage_id": genuine["passage_id"],
                    "genuine_cts_urn": genuine["cts_urn"],
                    "genuine_ref": genuine["canonical_ref"],
                    "genuine_text": genuine["text_content"],
                    "reason": reason,
                    "citations": cits,
                    "node": node,
                }
            )

        # --- Snapshot every touched citation + node BEFORE mutation -------
        snap = {
            "timestamp": ts,
            "citations_before": [
                {
                    "citation_id": c["citation_id"],
                    "kg_node_id": c["kg_node_id"],
                    "passage_id": c["passage_id"],
                    "old_ref": c["old_ref"],
                    "old_cts_urn": c["old_cts_urn"],
                    "old_work": c["old_work"],
                    "citation_type": c["citation_type"],
                    "confidence": c["confidence"],
                }
                for p in plan
                for c in p["citations"]
            ],
            "nodes_before": [
                {
                    "node_id": p["node"]["node_id"],
                    "label": p["node"]["label"],
                    "description": p["node"]["description"],
                    "metadata": p["node"]["metadata"],
                }
                for p in plan
            ],
            "plan": [
                {
                    "node_id": p["node_id"],
                    "citing_argument": p["citing_argument"],
                    "genuine_passage_id": p["genuine_passage_id"],
                    "genuine_ref": p["genuine_ref"],
                    "genuine_cts_urn": p["genuine_cts_urn"],
                    "reason": p["reason"],
                }
                for p in plan
            ],
        }
        snap_file = SNAPSHOT_DIR / "snapshot.json"
        snap_file.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSnapshot: {snap_file}")

        # --- Report the plan ---------------------------------------------
        print("\nRE-GROUNDING PLAN (confident matches):")
        for p in plan:
            print(f"  {p['node_id']}")
            print(f"    citing argument : {p['citing_argument']}")
            print(f"    -> genuine ref  : {p['genuine_ref']}  ({p['genuine_cts_urn']})")
            print(f"    citations to move: {len(p['citations'])}")
            print(f"    reason          : {p['reason']}")

        # --- Mutate -------------------------------------------------------
        if commit and plan:
            print("\nCommitting...")
            async with conn.transaction():
                for p in plan:
                    # 1. re-point citation rows
                    for c in p["citations"]:
                        await conn.execute(
                            "UPDATE free_will.passage_citations SET passage_id = $1::uuid "
                            "WHERE citation_id = $2::uuid",
                            p["genuine_passage_id"],
                            c["citation_id"],
                        )
                    # 2. correct the KG node: text, label, cts_urn in metadata
                    is_div = p["genuine_cts_urn"].startswith(
                        "urn:cts:latinLit:phi0474.phi053"
                    )
                    meta = _parse_metadata(p["node"]["metadata"])
                    meta["cts_urn"] = p["genuine_cts_urn"]
                    meta["canonical_ref"] = p["genuine_ref"]
                    meta["work_canonical_id"] = (
                        "urn:cts:latinLit:phi0474.phi053" if is_div
                        else "urn:cts:latinLit:phi0474.phi050"
                    )
                    meta["work_title"] = (
                        "De Divinatione" if is_div else "De Natura Deorum"
                    )
                    meta["db_passage_id"] = p["genuine_passage_id"]
                    meta["regrounded"] = {
                        "by": "rehome_cicero_semantic_2026_05_25",
                        "at": ts,
                        "from_wrong_work": p["citations"][0]["old_work"] if p["citations"] else None,
                        "citing_argument": p["citing_argument"],
                        "confidence": 1.0,
                        "method": "semantic-explicit-locus-verified-verbatim",
                    }
                    new_label = (
                        f"Cicero, De Divinatione, De Div. {p['genuine_ref']}"
                        if is_div
                        else f"Cicero, De Natura Deorum, De Nat. Deor. {p['genuine_ref']}"
                    )
                    await conn.execute(
                        "UPDATE free_will.kg_nodes "
                        "SET description = $1, label = $2, metadata = $3, updated_at = now() "
                        "WHERE node_id = $4",
                        p["genuine_text"],
                        new_label,
                        json.dumps(meta, ensure_ascii=False),
                        p["node_id"],
                    )
            print(f"Committed: {len(plan)} nodes re-grounded.")
        elif plan:
            print(f"\n[DRY-RUN] Would re-ground {len(plan)} nodes.")

        # --- Build the REVIEW file for unrecovered nodes -----------------
        _write_review(all_cic_nodes, node2args, arg_desc, set(CONFIDENT_MATCHES))

        # --- Summary ------------------------------------------------------
        recovered = len(CONFIDENT_MATCHES)
        div_total = sum(1 for n in all_cic_nodes if n.startswith("passage_cic_div_"))
        nd_total = sum(1 for n in all_cic_nodes if n.startswith("passage_cic_nat_deor_"))
        print(f"\n{'='*60}\nSUMMARY")
        print(f"  cic_div nodes total      : {div_total}")
        print(f"  cic_nat_deor nodes total : {nd_total}")
        print(f"  confidently re-grounded  : {recovered}")
        print(f"  flagged for manual review: {div_total + nd_total - recovered}")
        if not commit:
            print("\n[DRY-RUN] Pass --commit to write changes to the DB.")
    finally:
        await conn.close()
    return 0


def _write_review(
    all_cic_nodes: dict[str, dict],
    node2args: dict[str, list[str]],
    arg_desc: dict[str, dict[str, str]],
    recovered: set[str],
) -> None:
    """Emit data/corpus/REVIEW_cicero_unrecovered.md for nodes left untouched."""

    def _sort_key(nid: str) -> tuple[int, int]:
        is_nd = nid.startswith("passage_cic_nat_deor_")
        n = int(nid.rsplit("_", 1)[1])
        return (1 if is_nd else 0, n)

    unrecovered = sorted(
        (n for n in all_cic_nodes if n not in recovered), key=_sort_key
    )
    cited = [n for n in unrecovered if node2args.get(n)]
    orphan = [n for n in unrecovered if not node2args.get(n)]

    lines: list[str] = []
    lines.append("# Cicero passage-nodes — semantic re-grounding: UNRECOVERED")
    lines.append("")
    lines.append(
        "100 `passage_cic_div_*` + 22 `passage_cic_nat_deor_*` KG nodes were created "
        "from the WRONG corpus slots (Topica phi042 / Orator phi041). Their stored "
        "text is Topica/Orator prose and the trailing 'N' is a Topica/Orator section "
        "index, NOT a genuine *De Divinatione* / *De Natura Deorum* locus."
    )
    lines.append("")
    lines.append(
        "`scripts/rehome_cicero_semantic_2026_05_25.py` re-grounds a node ONLY when "
        "its single citing KG argument names one explicit Cicero locus AND the genuine "
        "passage there contains the quoted doctrine verbatim. The nodes below did NOT "
        "meet that bar and were left untouched (still pointing at Topica/Orator)."
    )
    lines.append("")
    lines.append("## Why each class is unrecoverable")
    lines.append("")
    lines.append(
        "- **Range-citing argument** — the citing argument references a whole book or "
        "section-range (e.g. 'De div. livre II §3, 9-72, 148'), so no single genuine "
        "passage is uniquely indicated; the fake N cannot be mapped 1:1 onto real "
        "sections without guessing."
    )
    lines.append(
        "- **Shared citation slot** — the node is cited by several arguments that point "
        "at DIFFERENT loci (e.g. `passage_cic_div_95` is cited by 6 arguments wanting "
        "De Div 2.21 / 2.90 / 2.96 / 2.97), so it cannot resolve to one passage."
    )
    lines.append(
        "- **No citing argument** — the node carries Topica/Orator text and is referenced "
        "by no argument at all, so there is no claim from which to recover a locus."
    )
    lines.append("")
    lines.append(f"## Cited-but-unrecovered nodes ({len(cited)})")
    lines.append("")
    for nid in cited:
        node = all_cic_nodes[nid]
        text = (node.get("description") or "").strip().replace("\n", " ")
        args = node2args.get(nid, [])
        klass = "shared citation slot" if len(args) > 1 else "range-citing argument"
        lines.append(f"### `{nid}`")
        lines.append("")
        lines.append(f"- **Class:** {klass} ({len(args)} citing argument(s))")
        lines.append(f"- **Current (WRONG) text:** {text[:240]}…")
        lines.append("- **Citing argument(s) and their claim:**")
        for a in args:
            d = arg_desc.get(a, {})
            claim = (d.get("label") or a)
            desc = (d.get("description") or "").strip().replace("\n", " ")
            lines.append(f"  - `{a}` — {claim}")
            if desc:
                lines.append(f"    - claim: {desc[:300]}…")
        lines.append("")

    lines.append(f"## Orphan nodes — no citing argument ({len(orphan)})")
    lines.append("")
    lines.append(
        "These carry Topica/Orator text and are linked only by structural "
        "`authored_by`/`part_of` edges. No argument references them, so no locus is "
        "recoverable. Candidates for deletion or manual re-grounding by Romain."
    )
    lines.append("")
    for nid in orphan:
        node = all_cic_nodes[nid]
        text = (node.get("description") or "").strip().replace("\n", " ")
        lines.append(f"- `{nid}` — current text: {text[:140]}…")
    lines.append("")

    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReview file: {REVIEW_PATH} "
          f"({len(cited)} cited-unrecovered + {len(orphan)} orphan)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="Write changes to DB (default: dry-run)")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main(args.commit)))
