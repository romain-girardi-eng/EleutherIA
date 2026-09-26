#!/usr/bin/env python3
"""Apply the verified passage-locus repairs of the 2026-09-26 independent audit. Dry-run first.

    PYTHONPATH=. python3 scripts/apply_2026_09_26_passage_loci.py --dry-run
    PYTHONPATH=. python3 scripts/apply_2026_09_26_passage_loci.py --apply

Input: data/audit/2026-09-26_independent_audit_passage_loci_ops.json. Every
operation was produced by locating the stored text of the passage in its
reference TEI (Perseus / First1KGreek / csel-dev) and re-checked by a second
reviewer. Modes:

* ``set``          — field must equal ``old``; it becomes ``new``.
* ``sub``          — replace the substring ``old`` by ``new``.
* ``disc_chapter`` — relabel "Discourses <book>.<chapter>" to the chapter where
  the Greek actually sits.
* ``book``         — Boethius ``metadata.book`` to the book where the text sits.
* ``set_any_pg``   — Methodius: the "PG 18.N" chunk numbers become Bonwetsch
  chapter.section loci.

``twin`` operations also update the corpus row named by ``metadata.db_passage_id``
so that ``check_kg_corpus_locus_parity`` keeps holding. The 59 Crito passages
filed as "Phaedo" get their own work node, and their part_of edges move to it.
Any operation whose precondition fails is skipped, so a re-run is a no-op.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import uuid

from scripts.verification_2026_09_24_lib import DATA, Store, meta, set_meta

SLUG = "independent_audit_passage_loci_2026_09_26"
OPS = DATA / "audit" / "2026-09-26_independent_audit_passage_loci_ops.json"
STAMP = "independent_audit_2026_09_26"
NOW = "2026-09-26 00:00:00+00:00"
CRITO = {
    "id": "work_plato_crito",
    "node_id": "work_plato_crito",
    "type": "work",
    "label": "Plato, Crito",
    "description": (
        "Plato's Crito (Κρίτων), set in Socrates's prison shortly before his execution (399 BCE): "
        "Crito urges escape, and Socrates answers with the speech of the personified Laws (50a-54d), "
        "arguing that a citizen who has freely stayed in the city has agreed to abide by its judgments. "
        "Text held here: Stephanus 43a-54e, PerseusDL canonical-greekLit tlg0059.tlg003 (Burnet, OCT vol. I)."
    ),
    "period": "Classical Greek",
    "school": "Platonist",
    "role": None,
    "alternative_names": "[]",
    "metadata": {
        "author": "Plato",
        "cts_urn": "urn:cts:greekLit:tlg0059.tlg003",
        "work_canonical_id": "urn:cts:greekLit:tlg0059.tlg003",
        "language": "grc",
        "editions": [{"editor": "Burnet", "series": "OCT", "year": "1900"}],
        STAMP: [{"finding": "passage_loci#0", "operation": "created: 59 Crito passages were filed under work_plato_phaedo"}],
    },
    "created_at": NOW,
    "updated_at": NOW,
}


def get(node: dict, field: str):
    return meta(node).get(field.split(".", 1)[1]) if field.startswith("metadata.") else node.get(field)


def put(node: dict, field: str, value) -> None:
    if field.startswith("metadata."):
        data = meta(node)
        data[field.split(".", 1)[1]] = value
        set_meta(node, data)
    else:
        node[field] = value


def stamp(node: dict, fid: str, field: str) -> None:
    data = meta(node)
    entries = data.setdefault(STAMP, [])
    if {"finding": fid, "field": field} not in entries:
        entries.append({"finding": fid, "field": field})
    set_meta(node, data)


def new_value(op: dict, current):
    mode = op["mode"]
    if mode == "set":
        return op["new"] if current == op["old"] else None
    if mode == "sub":
        return current.replace(op["old"], op["new"]) if isinstance(current, str) and op["old"] in current else None
    if mode == "disc_chapter":
        if not isinstance(current, str):
            return None
        out = re.sub(r"Discourses [IV]+\.\d+", "Discourses " + op["new"], current, count=1)
        return out if out != current else None
    if mode == "book":
        return op["new"] if current not in (None, op["new"]) else None
    if mode == "set_any_pg":
        return op["new"] if isinstance(current, str) and current.startswith("PG 18.") else None
    raise ValueError(mode)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run

    store = Store()
    nodes = store.nodes
    passages = {p["passage_id"]: p for p in store.rows["passages"]}
    counts: collections.Counter = collections.Counter()
    skipped, log, twin_updates = [], [], []
    for op in json.loads(OPS.read_text()):
        node = nodes.get(op["node"])
        if node is None:
            skipped.append((op["fid"], op["node"], "node absent"))
            continue
        current = get(node, op["field"])
        value = new_value(op, current)
        if value is None:
            skipped.append((op["fid"], op["node"], f"precondition failed ({current!r})"))
            continue
        put(node, op["field"], value)
        stamp(node, op["fid"], op["field"])
        counts["node_field"] += 1
        if op["twin"]:
            row = passages.get(str(meta(node).get("db_passage_id") or ""))
            key = op["field"].split(".", 1)[1]
            if row is not None and row.get(key) == current:
                row[key] = value
                counts["corpus_twin"] += 1
                twin_updates.append((row["passage_id"], op["field"], current, value, op["fid"]))
        log.append((op["fid"], op["node"], op["field"], current, value))

    # Other KG nodes sharing the same corpus row (e.g. the ``_en`` translation
    # node of a Greek passage) take the same locus.
    by_row = collections.defaultdict(list)
    for n in store.rows["nodes"]:
        pid = meta(n).get("db_passage_id") if n.get("type") == "passage" else None
        if pid:
            by_row[str(pid)].append(n)
    for pid, field, old, value, fid in twin_updates:
        for n in by_row.get(pid, []):
            if get(n, field) == old:
                put(n, field, value)
                stamp(n, fid, field)
                counts["shared_row_node"] += 1
                log.append((fid, n["id"], field, old, value))

    # Crito: own work node, part_of edges moved off the Phaedo
    if "work_plato_crito" not in nodes:
        store.rows["nodes"].append(json.loads(json.dumps(CRITO)))
        counts["work_created"] += 1
    crito_ids = {op["node"] for op in json.loads(OPS.read_text()) if op["fid"] == "passage_loci#0"}
    for e in store.edges:
        if e["relation"] == "part_of" and e["source"] in crito_ids and e["target"] == "work_plato_phaedo":
            m = e.get("metadata") or {}
            m = json.loads(m) if isinstance(m, str) else dict(m)
            m[STAMP] = {"finding": "passage_loci#0", "previous_target": "work_plato_phaedo"}
            e["metadata"] = json.dumps(m, ensure_ascii=False) if isinstance(e.get("metadata"), str) else m
            e["target"] = e["target_id"] = "work_plato_crito"
            counts["part_of_moved"] += 1
    if counts["work_created"] and not any(e["source"] == "work_plato_crito" and e["relation"] == "authored_by"
                                          for e in store.edges):
        store.rows["edges"].append({
            "edge_id": str(uuid.uuid5(uuid.NAMESPACE_URL, "eleutheria:work_plato_crito:authored_by")),
            "source": "work_plato_crito", "source_id": "work_plato_crito",
            "target": "person_plato_428_348bce_a1b2c3d4", "target_id": "person_plato_428_348bce_a1b2c3d4",
            "relation": "authored_by", "weight": 1.0, "created_at": NOW,
            "metadata": {STAMP: {"finding": "passage_loci#0"}},
        })
        counts["edge_added"] += 1

    summary = store.commit(SLUG, apply=apply)
    if apply:
        (DATA / "audit" / f"2026-09-26_{SLUG}_apply_log.json").write_text(
            json.dumps(log, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"mode": "apply" if apply else "dry_run", "counts": counts,
                      "skipped": skipped, "changes": summary}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
