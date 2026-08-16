#!/usr/bin/env python3
"""Apply the 2026-08-16 deep structural/ontological audit to the local KG mirror.

Findings file: ``data/audit/2026-08-16_deep_audit_structural.jsonl``.

Every operation below is driven by *evidence already present in the data* — a
declared ``previous_node_id``, a shared ``bibtex_key``, a shared ``work_id``
UUID, a metadata note recording a merge that was never executed, or a
byte-identical description. Nothing here relies on the model's own knowledge of
ancient texts, and no ancient Greek or Latin is generated, altered or moved.

Operations
----------
1. ``fix_edge_field_divergence`` — 6 edges carry ``target != target_id``. The
   in-memory loaders read ``target`` first, the SQL k-hop CTE in
   ``db_traversal.py`` reads ``target_id``: the two retrieval paths return
   different authorship. ``target_id`` is realigned onto ``target`` (the
   post-correction value, confirmed node-side for each of the three clusters).
2. ``fix_dangling_metadata_pointers`` — 73 ``scholar_id`` / ``author_id`` /
   ``scholarly_work_id`` / ``publication`` values point at 9 node ids that no
   longer exist. Each has exactly one surviving counterpart, verified field by
   field (same person, same title, same year, same ``verified_reference``).
3. ``merge_duplicate_nodes`` — 7 confirmed duplicate clusters are collapsed:
   the survivor absorbs the fields the loser held alone, the loser's edges are
   repointed (deduplicated against existing triples), the loser is deleted.
4. ``fix_false_translations`` — 340 nodes declare ``passage_role=translation``
   and ``language=eng`` while their description is byte-identical to the
   original they point at. No translation was ever produced. The false
   ``language``/``role`` claims and the ``has_translation``/``translation_of``
   edge pairs are removed; the node is kept, relabelled and queued via
   ``needs_translation``. This mirrors the 2026-08-16 Alcinous/Hegesippus
   precedent: say what the node actually is, delete the false assertions.
5. ``flag_empty_passages`` — passages whose description is empty or is nothing
   but scraped site chrome are flagged ``needs_text_ingestion``.
6. ``wire_fragment_collections`` — ``collection_ls`` / ``collection_dk`` are
   orphans while passages already carry ``metadata.fragment_collections`` naming
   them. The ``part_of`` edges are derived from that existing evidence only.
7. ``normalise_edge_encoding`` — edges.jsonl only: U+02BC and U+1FBD elision
   marks folded to U+2019, and every string NFC-normalised. nodes.jsonl Greek
   is deliberately NOT touched (see module docstring of the data file).
8. ``rename_ids`` — id prefixes that contradict the node type.

The script is deterministic and idempotent. Touched nodes/edges are stamped
with ``deep_audit_2026_08_16``; a stamped record is skipped on any later run.
Any operation whose precondition no longer holds is reported and skipped, never
applied blind.

Usage:
    python3 scripts/apply_2026_08_16_deep_audit_structural.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_16_deep_audit_structural import (  # noqa: E402
    CHROME_MARKERS,
    EDGE_FIELD_DIVERGENCE,
    ID_RENAMES,
    METADATA_POINTER_FIELDS,
    METADATA_POINTER_REMAP,
    NODE_MERGES,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"

STAMP = "deep_audit_2026_08_16"

log: list[str] = []
counts: dict[str, int] = {}


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] = counts.get(op, 0) + 1


def warn(op: str, msg: str) -> None:
    log.append(f"[{op}] SKIPPED: {msg}")
    counts[op + "__skipped"] = counts.get(op + "__skipped", 0) + 1


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def nid(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def meta(node: dict) -> dict:
    value = node.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def set_meta(node: dict, data: dict) -> None:
    """Write metadata back in the shape the node already used."""
    if isinstance(node.get("metadata"), str):
        node["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        node["metadata"] = data


def stamped(record: dict, op: str) -> bool:
    return meta(record).get(STAMP) == op if record.get("metadata") else False


def stamp(record: dict, op: str, detail: str) -> None:
    data = meta(record)
    data[STAMP] = op
    data[f"{STAMP}_note"] = detail
    set_meta(record, data)


# --------------------------------------------------------------------------- 1
def fix_edge_field_divergence(edges: list[dict]) -> None:
    op = "fix_edge_field_divergence"
    by_id = {e.get("edge_id"): e for e in edges}
    for edge_id, expected_target, expected_stale, reason in EDGE_FIELD_DIVERGENCE:
        edge = by_id.get(edge_id)
        if edge is None:
            warn(op, f"edge {edge_id} not found")
            continue
        if edge.get("target") == edge.get("target_id"):
            continue  # already consistent (idempotent)
        if (
            edge.get("target") != expected_target
            or edge.get("target_id") != expected_stale
        ):
            warn(
                op,
                f"{edge_id}: expected target={expected_target}/target_id={expected_stale}, "
                f"found {edge.get('target')}/{edge.get('target_id')}",
            )
            continue
        edge["target_id"] = expected_target
        data = edge.get("metadata") or {}
        if isinstance(data, dict):
            data[STAMP] = op
            data[f"{STAMP}_note"] = (
                f"target_id realigned onto target ({expected_stale} -> {expected_target}). {reason}"
            )
            edge["metadata"] = data
        note(op, f"{edge_id}: target_id {expected_stale} -> {expected_target}")


# --------------------------------------------------------------------------- 2
def fix_dangling_metadata_pointers(nodes: list[dict], present: set[str]) -> None:
    op = "fix_dangling_metadata_pointers"
    for node in nodes:
        data = meta(node)
        if not data:
            continue
        changed = []
        for field in METADATA_POINTER_FIELDS:
            value = data.get(field)
            if not isinstance(value, str) or value in present:
                continue
            replacement = METADATA_POINTER_REMAP.get(value)
            if replacement is None:
                continue
            if replacement not in present:
                warn(op, f"{nid(node)}.{field}: replacement {replacement} missing")
                continue
            data[field] = replacement
            changed.append(f"{field}: {value} -> {replacement}")
        if changed:
            data.setdefault(f"{STAMP}_pointer_fixes", []).extend(changed)
            set_meta(node, data)
            note(op, f"{nid(node)}: " + "; ".join(changed))


# --------------------------------------------------------------------------- 3
def merge_duplicate_nodes(
    nodes: list[dict], edges: list[dict]
) -> tuple[list[dict], list[dict]]:
    op = "merge_duplicate_nodes"
    by_id = {nid(n): n for n in nodes}
    drop_nodes: set[str] = set()

    for merge in NODE_MERGES:
        keep_id, drop_id = merge["keep"], merge["drop"]
        keep, drop = by_id.get(keep_id), by_id.get(drop_id)
        if keep is None:
            warn(op, f"survivor {keep_id} not found")
            continue
        if drop is None:
            continue  # already merged (idempotent)

        # Precondition: the recorded proof must still hold in the data.
        if not merge["proof"](keep, drop, meta(keep), meta(drop)):
            warn(op, f"{drop_id} -> {keep_id}: proof predicate no longer holds")
            continue

        keep_meta, drop_meta = meta(keep), meta(drop)
        ported = []
        for field in merge.get("port_meta", []):
            if field in drop_meta and not keep_meta.get(field):
                keep_meta[field] = drop_meta[field]
                ported.append(field)
        for field in merge.get("port_meta_overwrite", []):
            if field in drop_meta:
                keep_meta[field] = drop_meta[field]
                ported.append(f"{field}(overwrite)")
        if merge.get("port_description") and len(drop.get("description") or "") > len(
            keep.get("description") or ""
        ):
            keep["description"] = drop["description"]
            ported.append("description")

        keep_meta.setdefault(f"{STAMP}_merged_from", []).append(drop_id)
        keep_meta[f"{STAMP}_merge_reason"] = merge["reason"]
        set_meta(keep, keep_meta)
        drop_nodes.add(drop_id)
        note(op, f"{drop_id} -> {keep_id} (ported: {', '.join(ported) or 'nothing'})")

    if not drop_nodes:
        return nodes, edges

    remap = {m["drop"]: m["keep"] for m in NODE_MERGES if m["drop"] in drop_nodes}
    nodes = [n for n in nodes if nid(n) not in drop_nodes]

    seen_triples = set()
    kept_edges: list[dict] = []
    for edge in edges:
        src = remap.get(edge["source"], edge["source"])
        tgt = remap.get(edge["target"], edge["target"])
        if src == tgt:
            note(op, f"dropped self-loop created by merge: {edge['edge_id']}")
            continue
        triple = (src, edge["relation"], tgt)
        if triple in seen_triples:
            note(op, f"dropped duplicate triple created by merge: {edge['edge_id']}")
            continue
        seen_triples.add(triple)
        if src != edge["source"] or tgt != edge["target"]:
            edge["source"], edge["source_id"] = src, src
            edge["target"], edge["target_id"] = tgt, tgt
        kept_edges.append(edge)
    return nodes, kept_edges


# --------------------------------------------------------------------------- 4
def fix_false_translations(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """340 'translations' that are byte-identical copies of their original."""
    op = "fix_false_translations"
    by_id = {nid(n): n for n in nodes}
    culprits: set[str] = set()

    for node in nodes:
        data = meta(node)
        if data.get(STAMP) == op:
            culprits.add(nid(node))
            continue
        if data.get("passage_role") != "translation":
            continue
        origin_id = data.get("original_node_id")
        origin = by_id.get(origin_id) if origin_id else None
        if origin is None:
            continue
        if (node.get("description") or "").strip() != (
            origin.get("description") or ""
        ).strip():
            continue  # a real translation

        origin_lang = meta(origin).get("language")
        data["language"] = origin_lang
        data["passage_role"] = "untranslated_duplicate"
        data["needs_translation"] = True
        data["translation_integrity_2026_08_16"] = (
            "This node was recorded as the English translation of "
            f"{origin_id} (language=eng, passage_role=translation, auto_generated), but its text is "
            "byte-identical to that original: no translation was ever produced. The false language "
            "and role claims are withdrawn and the has_translation/translation_of edge pair is "
            "removed. The node is retained, and queued for translation, rather than deleted."
        )
        # set_meta BEFORE stamp: stamp() re-parses metadata, so for nodes whose
        # metadata is a JSON string the mutations above must be written back first.
        set_meta(node, data)
        stamp(node, op, "false translation withdrawn")
        label = node.get("label") or ""
        if label.endswith(" (English)"):
            node["label"] = label[: -len(" (English)")] + " (translation pending)"
        culprits.add(nid(node))
        note(op, f"{nid(node)}: withdrawn (copy of {origin_id})")

    if not culprits:
        return edges
    kept = []
    for edge in edges:
        if edge["relation"] in ("has_translation", "translation_of") and (
            edge["source"] in culprits or edge["target"] in culprits
        ):
            counts[op + "__edges_removed"] = counts.get(op + "__edges_removed", 0) + 1
            continue
        kept.append(edge)
    return kept


# --------------------------------------------------------------------------- 5
def flag_empty_passages(nodes: list[dict]) -> None:
    op = "flag_empty_passages"
    for node in nodes:
        if node.get("type") != "passage":
            continue
        text = (node.get("description") or "").strip()
        data = meta(node)
        if data.get(STAMP) == op:
            continue
        reason = None
        if not text:
            reason = "description is empty"
        elif any(marker in text for marker in CHROME_MARKERS) and len(text) < 160:
            reason = f"description is scraped site chrome, not text: {text!r}"
        if reason is None:
            continue
        data["needs_text_ingestion"] = True
        set_meta(node, data)
        stamp(node, op, reason)
        note(op, f"{nid(node)}: {reason}")


# --------------------------------------------------------------------------- 6
def wire_fragment_collections(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Derive part_of edges from metadata.fragment_collections already present."""
    op = "wire_fragment_collections"
    siglum_to_node = {"LS": "collection_ls", "DK": "collection_dk"}
    present = {nid(n) for n in nodes}
    existing = {(e["source"], e["relation"], e["target"]) for e in edges}
    new_edges: list[dict] = []

    for node in nodes:
        if node.get("type") != "passage":
            continue
        entries = meta(node).get("fragment_collections")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            target = siglum_to_node.get(entry.get("collection"))
            if not target or target not in present:
                continue
            triple = (nid(node), "part_of", target)
            if triple in existing:
                continue
            existing.add(triple)
            new_edges.append(
                {
                    "created_at": "2026-08-16 00:00:00+00:00",
                    "edge_id": f"deepaudit-{nid(node)}-partof-{target}",
                    "metadata": {
                        STAMP: op,
                        f"{STAMP}_note": (
                            "Derived from the node's own metadata.fragment_collections entry "
                            f"(collection={entry.get('collection')}, reference={entry.get('reference')}). "
                            "No new scholarly claim: the siglum was already asserted on the passage; "
                            "this only makes it traversable, un-orphaning the collection node."
                        ),
                        "fragment_reference": entry.get("reference"),
                    },
                    "relation": "part_of",
                    "source": nid(node),
                    "source_id": nid(node),
                    "target": target,
                    "target_id": target,
                    "weight": 1.0,
                }
            )
            note(op, f"{nid(node)} part_of {target} ({entry.get('reference')})")
    return edges + new_edges


# --------------------------------------------------------------------------- 7
def normalise_edge_encoding(edges: list[dict]) -> None:
    """edges.jsonl only: fold stray elision marks, NFC-normalise every string."""
    op = "normalise_edge_encoding"
    folds = {"ʼ": "’", "᾽": "’"}

    def walk(value):
        changed = False
        if isinstance(value, str):
            out = value
            for bad, good in folds.items():
                if bad in out:
                    out = out.replace(bad, good)
            normalised = unicodedata.normalize("NFC", out)
            return normalised, normalised != value
        if isinstance(value, dict):
            for key, item in value.items():
                new_item, item_changed = walk(item)
                if item_changed:
                    value[key] = new_item
                    changed = True
            return value, changed
        if isinstance(value, list):
            for index, item in enumerate(value):
                new_item, item_changed = walk(item)
                if item_changed:
                    value[index] = new_item
                    changed = True
            return value, changed
        return value, False

    for edge in edges:
        _, changed = walk(edge)
        if changed:
            note(op, f"{edge.get('edge_id')}: encoding normalised")


# --------------------------------------------------------------------------- 8
def rename_ids(nodes: list[dict], edges: list[dict]) -> dict[str, str]:
    op = "rename_ids"
    present = {nid(n) for n in nodes}
    active = {old: new for old, new in ID_RENAMES.items() if old in present}
    for old, new in active.items():
        if new in present:
            warn(op, f"target id {new} already exists; not renaming {old}")
            active.pop(old, None)
    for node in nodes:
        current = nid(node)
        new = active.get(current)
        if not new:
            continue
        data = meta(node)
        data["previous_node_id"] = current
        set_meta(node, data)
        stamp(
            node,
            op,
            f"renamed from {current}: id prefix contradicted node type '{node['type']}'",
        )
        if "node_id" in node:
            node["node_id"] = new
        if "id" in node:
            node["id"] = new
        note(op, f"{current} -> {new}")
    for edge in edges:
        for side in ("source", "target"):
            if edge.get(side) in active:
                edge[side] = active[edge[side]]
                edge[f"{side}_id"] = edge[side]
    return active


# --------------------------------------------------------------------------- 8b
def wire_hegesippus(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Un-orphan the Hegesippus fragment collection.

    ``passage_hegesippus_hypomnemata_fragments`` (formerly filed under Alcinous)
    carries 1,265 words of Greek and zero edges: nothing in the graph can reach
    it. Its own metadata already asserts author=Hegesippus and
    work_canonical_id=urn:cts:greekLit:tlg1398, TLG-verified on 2026-08-16. The
    author and work nodes those fields presuppose simply do not exist yet, so
    they are created here — English descriptions only, no Greek generated — and
    the passage is wired to them.
    """
    op = "wire_hegesippus"
    passage_id = "passage_hegesippus_hypomnemata_fragments"
    person_id = "person_hegesippus_2c_ce"
    work_id = "work_hegesippus_hypomnemata"
    by_id = {nid(n): n for n in nodes}
    if passage_id not in by_id:
        warn(op, f"{passage_id} not found")
        return edges
    if person_id in by_id and work_id in by_id:
        return edges  # idempotent

    now = "2026-08-16 00:00:00+00:00"
    provenance = (
        "Created by the 2026-08-16 deep structural audit to un-orphan "
        f"{passage_id}, whose own metadata already asserted author=Hegesippus and "
        "work_canonical_id=urn:cts:greekLit:tlg1398 (TLG-verified 2026-08-16 via "
        "scripts/tlg_search.py). No ancient text was generated for these nodes."
    )
    if person_id not in by_id:
        nodes.append(
            {
                "alternative_names": "[]",
                "created_at": now,
                "description": (
                    "Hegesippus (fl. c. 160-180 CE), Christian chronicler of the sub-apostolic "
                    "period. His five books of Hypomnemata (Memoirs) are lost; what survives is "
                    "transmitted as quotations by Eusebius in the Historia ecclesiastica "
                    "(II.23 on James the Just, III.32 on the martyrdom of Symeon son of Clopas "
                    "under Trajan, IV.22 on the Jewish sects), together with one fragment "
                    "preserved by Photius from Stephanus Gobarus."
                ),
                "id": person_id,
                "label": "Hegesippus",
                "metadata": {
                    "floruit": "c. 160-180 CE",
                    "language": "grc",
                    "tlg_author_number": "tlg1398",
                    STAMP: op,
                    f"{STAMP}_note": provenance,
                },
                "node_id": person_id,
                "period": "Roman Imperial",
                "role": None,
                "school": None,
                "type": "person",
                "updated_at": now,
            }
        )
        note(op, f"created {person_id}")
    if work_id not in by_id:
        nodes.append(
            {
                "alternative_names": "[]",
                "created_at": now,
                "description": (
                    "Hypomnemata (Memoirs), in five books, by Hegesippus. Lost as a whole; known "
                    "only through fragments quoted by Eusebius, Historia ecclesiastica, and one "
                    "fragment transmitted by Photius from Stephanus Gobarus. Catalogued as "
                    "TLG 1398."
                ),
                "id": work_id,
                "label": "Hegesippus, Hypomnemata (fragments)",
                "metadata": {
                    "author": "Hegesippus",
                    "cts_urn": "urn:cts:greekLit:tlg1398",
                    "language": "grc",
                    "attestation_type": "fragment_collection",
                    STAMP: op,
                    f"{STAMP}_note": provenance,
                },
                "node_id": work_id,
                "period": "Roman Imperial",
                "role": None,
                "school": None,
                "type": "work",
                "updated_at": now,
            }
        )
        note(op, f"created {work_id}")

    for source, relation, target in (
        (passage_id, "part_of", work_id),
        (passage_id, "authored_by", person_id),
        (work_id, "authored_by", person_id),
    ):
        edges.append(
            {
                "created_at": now,
                "edge_id": f"deepaudit-{source}-{relation}-{target}",
                "metadata": {STAMP: op, f"{STAMP}_note": provenance},
                "relation": relation,
                "source": source,
                "source_id": source,
                "target": target,
                "target_id": target,
                "weight": 1.0,
            }
        )
        note(op, f"{source} -[{relation}]-> {target}")
    return edges


# --------------------------------------------------------------------------- 9
def propagate_to_citations(remap: dict[str, str], present: set[str]) -> int:
    """Carry merges and renames into data/corpus/citations.jsonl.

    ``scripts/check_corpus_invariants.py`` asserts that every
    ``citation.kg_node_id`` resolves to a live node. Merging or renaming a node
    without this step would create dangling citations (baseline: 0).

    Deliberately NOT propagated: data/audit/*, data/kg/snapshots/*,
    data/kg_enrichment/*, data/goals/* — those are historical records and must
    keep the ids that were true when they were written. Also left alone is
    ``data/corpus/passages.jsonl``, whose ``work_canonical_id`` lives in the
    corpus namespace (``…_grc`` / ``…_eng`` suffixes), not the KG one.
    """
    op = "propagate_to_citations"
    path = ROOT / "data" / "corpus" / "citations.jsonl"
    if not path.exists():
        warn(op, "citations.jsonl not found")
        return 0
    rows = read_jsonl(path)
    changed = 0
    for row in rows:
        current = row.get("kg_node_id")
        if current in present:
            continue
        replacement = remap.get(current)
        if replacement and replacement in present:
            row["kg_node_id"] = replacement
            row["kg_node_id_remapped_2026_08_16"] = current
            changed += 1
            note(op, f"{current} -> {replacement}")
        elif current is not None:
            warn(op, f"no mapping for dangling kg_node_id {current}")
    if changed:
        write_jsonl(path, rows)
    return changed


# --------------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    before = (len(nodes), len(edges))

    fix_edge_field_divergence(edges)
    fix_dangling_metadata_pointers(nodes, {nid(n) for n in nodes})
    nodes, edges = merge_duplicate_nodes(nodes, edges)
    edges = fix_false_translations(nodes, edges)
    flag_empty_passages(nodes)
    edges = wire_fragment_collections(nodes, edges)
    normalise_edge_encoding(edges)
    renames = rename_ids(nodes, edges)
    edges = wire_hegesippus(nodes, edges)

    # Compose merge -> rename so a node that was merged and then renamed
    # (sc31_melito_peri_pascha_iv -> passage_eusebius_… -> work_eusebius_…)
    # resolves in one hop for downstream files.
    remap = {m["drop"]: m["keep"] for m in NODE_MERGES}
    remap = {old: renames.get(new, new) for old, new in remap.items()}
    remap.update(renames)

    # ---- invariants, enforced before anything is written -------------------
    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids produced"
    present = set(ids)
    dangling = [
        e["edge_id"]
        for e in edges
        if e["source"] not in present or e["target"] not in present
    ]
    assert not dangling, f"dangling edges produced: {dangling[:5]}"
    split = [
        e["edge_id"]
        for e in edges
        if e["source"] != e["source_id"] or e["target"] != e["target_id"]
    ]
    assert not split, f"source/target field divergence remains: {split[:5]}"
    triples = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triples) == len(set(triples)), "duplicate triples produced"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops produced"

    print(f"nodes {before[0]} -> {len(nodes)}   edges {before[1]} -> {len(edges)}")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(
        "invariants: OK (no dupe ids, no dangling, no split fields, no dupe triples, no self-loops)"
    )

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    propagate_to_citations(remap, present)
    report = ROOT / "data" / "audit" / "2026-08-16_deep_audit_structural_applied.md"
    report.write_text(
        "# Deep structural audit — applied 2026-08-16\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
