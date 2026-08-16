#!/usr/bin/env python3
"""Wave 6: repair the dialectical layer and the editorial-synthesis passages.

See ``data_2026_08_17_dialectical_repairs.py`` for the evidence behind every edit
— each verdict names the print it was checked against, or says it could not be.

Four lots:
  1. the 21 dialectical edges of the ``g5_deep_2026_06_15`` batch, re-verified one
     by one, plus the person-level legs of the same audit finding and one
     mistargeted ``supports``;
  2. passage nodes that are editorial syntheses sharing a primary's CTS URN —
     detected at apply time, never hard-coded;
  3. 44 Tertullian passages whose id and text name different works;
  4. nothing (the R16 gate lives in ``scripts/check_ingestion_rules.py``); the
     applier calls that gate on the one node it creates.

Usage:
    python3 scripts/apply_2026_08_17_dialectical_repairs.py            # dry run
    python3 scripts/apply_2026_08_17_dialectical_repairs.py --write    # apply

Idempotent: re-running after a successful write is a no-op. Every edit
re-checks its own precondition at apply time and skips, loudly, if the graph has
moved. Backups are written to ``*.bak-dialectical`` before anything is changed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_2026_08_17_dialectical_repairs import (  # noqa: E402
    DIALECTICAL_RELATIONS,
    G5_EDGE_VERDICTS,
    LOT2_EXPECTED,
    LOT2_POLICY,
    MISTARGETED_SUPPORTS,
    NODE_CLAIM_CORRECTIONS,
    PERSON_LEVEL_REPAIRS,
    STAMP,
    TERTULLIAN_EMPTIED_WORKS,
    TERTULLIAN_METADATA_KEYS,
    TERTULLIAN_NEW_WORK_EDGE,
    TERTULLIAN_NEW_WORK_NODE,
    TERTULLIAN_REATTRIBUTIONS,
    detect_editorial_syntheses,
)

ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
CITATIONS_PATH = ROOT / "data" / "corpus" / "citations.jsonl"
RULES_CHECKER = ROOT / "scripts" / "check_ingestion_rules.py"
BAK_SUFFIX = ".bak-dialectical"

log: list[str] = []
counts: dict[str, int] = {}
skipped: list[str] = []


def note(op: str, msg: str) -> None:
    log.append(f"[{op}] {msg}")
    counts[op] = counts.get(op, 0) + 1


def warn(op: str, msg: str) -> None:
    line = f"[{op}] SKIPPED: {msg}"
    log.append(line)
    skipped.append(line)
    counts[op + "__skipped"] = counts.get(op + "__skipped", 0) + 1


# --------------------------------------------------------------------------- io
def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def nid(node: dict) -> str:
    return node.get("node_id") or node.get("id") or ""


def meta(obj: dict) -> dict:
    """Read metadata, which some rows carry as a JSON *string*."""
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value if isinstance(value, dict) else {}


def set_meta(obj: dict, data: dict) -> None:
    """Write metadata back in the shape it was read in — string stays string."""
    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(data, ensure_ascii=False)
    else:
        obj["metadata"] = data


def stamp(obj: dict, op: str, why: str) -> None:
    data = meta(obj)
    data[STAMP] = op
    data[f"{STAMP}_note"] = why
    set_meta(obj, data)


# ---------------------------------------------------------------- lot 1 helpers
def apply_edge_verdict(edge: dict, spec: dict, triples: set, drop: set) -> None:
    """Apply one re-verification verdict to one edge. Precondition-checked."""
    edge_id = edge["edge_id"]
    verdict = spec["verdict"]
    data = meta(edge)

    # idempotency: this edge has already been through this wave
    if data.get(STAMP):
        return

    expected = spec.get("expected_relation")
    if expected and edge["relation"] != expected:
        warn(
            f"g5_{verdict}",
            f"{edge_id}: relation is {edge['relation']!r}, expected {expected!r} "
            f"— the graph moved since the verdict was written; not touched",
        )
        return

    if verdict == "delete":
        drop.add(edge_id)
        note("g5_delete", f"{edge_id} {spec['pair']}: {spec['why'][:130]}")
        return

    if verdict == "retype":
        new_relation = spec["new_relation"]
        new_triple = (edge["source"], new_relation, edge["target"])
        if new_triple in triples:
            drop.add(edge_id)
            note(
                "g5_retype",
                f"{edge_id}: {edge['relation']} -> {new_relation} already asserted; edge dropped",
            )
            return
        triples.discard((edge["source"], edge["relation"], edge["target"]))
        triples.add(new_triple)
        data["retyped_from"] = edge["relation"]
        edge["relation"] = new_relation
        note("g5_retype", f"{edge_id} {spec['pair']}: -> {new_relation}")

    if verdict == "flag":
        data["verification"] = "unverified_g5"
        data["dialectical_claim_unsupported"] = True
        if spec.get("confidence") is not None:
            edge["confidence"] = spec["confidence"]
            data["confidence"] = spec["confidence"]
        data[f"{STAMP}_note"] = spec["why"]
        data[STAMP] = "flag"
        set_meta(edge, data)
        note("g5_flag_unverified", f"{edge_id} {spec['pair']}")
        return

    # keep / retype both get the full attestation payload
    if spec.get("attested_by"):
        data["attested_by"] = spec["attested_by"]
    if spec.get("proposition"):
        data["proposition"] = spec["proposition"]
    if spec.get("relation_basis"):
        data["relation_basis"] = spec["relation_basis"]
    if spec.get("scope_note"):
        data["scope_note"] = spec["scope_note"]
    if spec.get("audit_finding"):
        data["audit_finding"] = spec["audit_finding"]
    if spec.get("why"):
        data[f"{STAMP}_why"] = spec["why"]
    if spec.get("followup"):
        data["followup"] = spec["followup"]
    if spec.get("confidence") is not None:
        edge["confidence"] = spec["confidence"]
        data["confidence"] = spec["confidence"]
    data["verification"] = "reverified_2026_08_17"
    data[STAMP] = verdict
    set_meta(edge, data)
    if verdict == "keep":
        note("g5_keep_attested", f"{edge['edge_id']} {spec['pair']}")


# ------------------------------------------------------------------------ main
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write",
        action="store_true",
        help="apply the changes (default is a dry run that writes nothing)",
    )
    parser.add_argument("--dry-run", action="store_true", help="explicit no-op default")
    args = parser.parse_args()
    dry_run = not args.write

    nodes = read_jsonl(NODES_PATH)
    edges = read_jsonl(EDGES_PATH)
    citations = read_jsonl(CITATIONS_PATH) if CITATIONS_PATH.exists() else []
    before = (len(nodes), len(edges), len(citations))

    N = {nid(n): n for n in nodes}
    by_edge = {e.get("edge_id"): e for e in edges}
    triples = {(e["source"], e["relation"], e["target"]) for e in edges}
    drop_edge_ids: set[str] = set()
    new_nodes: list[dict] = []
    new_edges: list[dict] = []

    # ==================================================================
    # LOT 1 — dialectical edges
    # ==================================================================
    for edge_id, spec in G5_EDGE_VERDICTS.items():
        edge = by_edge.get(edge_id)
        if edge is None:
            if spec["verdict"] != "delete":  # a delete that already happened is a no-op
                warn("g5_" + spec["verdict"], f"{edge_id} not found ({spec['pair']})")
            continue
        provenance = meta(edge).get("provenance")
        if provenance != "g5_deep_2026_06_15" and not meta(edge).get(STAMP):
            warn(
                "g5_" + spec["verdict"],
                f"{edge_id}: provenance is {provenance!r}, not the g5 batch",
            )
            continue
        apply_edge_verdict(edge, spec, triples, drop_edge_ids)

    for edge_id, spec in {**PERSON_LEVEL_REPAIRS, **MISTARGETED_SUPPORTS}.items():
        edge = by_edge.get(edge_id)
        if edge is None:
            if spec["verdict"] != "delete":
                warn(
                    "triangle_" + spec["verdict"],
                    f"{edge_id} not found ({spec['pair']})",
                )
            continue
        apply_edge_verdict(edge, spec, triples, drop_edge_ids)

    # a node whose own description misstates its scholar
    for fix in NODE_CLAIM_CORRECTIONS:
        node = N.get(fix["node"])
        if node is None:
            warn("fix_node_claim", f"{fix['node']} not found")
            continue
        current = node.get(fix["field"]) or ""
        if current == fix["new_description"]:
            continue  # idempotent
        if fix["expect_contains"] not in current:
            warn(
                "fix_node_claim",
                f"{fix['node']}: {fix['field']} no longer contains "
                f"{fix['expect_contains']!r}; not rewritten",
            )
            continue
        node[fix["field"]] = fix["new_description"]
        data = meta(node)
        data["attested_by"] = fix["attested_by"]
        data[f"{STAMP}_claim_fix"] = fix["why"]
        set_meta(node, data)
        note("fix_node_claim", f"{fix['node']}: description corrected")

    # ==================================================================
    # LOT 2 — editorial-synthesis passages
    # ==================================================================
    pairs, ambiguous, stats = detect_editorial_syntheses(nodes, nid, meta)
    print("lot 2 detector:", json.dumps(stats))
    for shape in ambiguous:
        warn(
            "lot2_ambiguous",
            f"{shape[0]['synthesis']} resolves to {len(shape)} primaries "
            f"({', '.join(p['primary'] for p in shape)}); left alone",
        )

    # A node already reclassified by a previous run is invisible to the detector
    # (its cts_urn is gone), so count it towards the expected population — the
    # guard must fire on a change of shape, not on a second run.
    already = sum(
        1
        for n in nodes
        if n.get("type") == "passage"
        and meta(n).get("passage_role") == LOT2_POLICY["passage_role"]
    )
    stats["already_classified"] = already
    expected = LOT2_EXPECTED["detected_syntheses"]
    tol = LOT2_EXPECTED["tolerance_pct"] / 100
    population = stats["detected_syntheses"] + already
    if not (expected * (1 - tol) <= population <= expected * (1 + tol)):
        print(
            f"REFUSING: detector found {stats['detected_syntheses']} syntheses "
            f"(+{already} already classified) = {population}, expected ~{expected} "
            f"(+/-{LOT2_EXPECTED['tolerance_pct']}%). The graph has changed shape; "
            "re-run the hand sample before applying.",
            file=sys.stderr,
        )
        return 2

    for pair in pairs:
        synthesis = N.get(pair["synthesis"])
        primary = N.get(pair["primary"])
        if synthesis is None or primary is None:
            warn("lot2_classify", f"{pair['synthesis']} or its primary vanished")
            continue
        data = meta(synthesis)
        if data.get("passage_role") == LOT2_POLICY["passage_role"]:
            continue  # idempotent
        # precondition re-check: the two must still collide on the identity key
        if meta(primary).get("cts_urn") != pair["cts_urn"]:
            warn(
                "lot2_classify",
                f"{pair['synthesis']}: primary {pair['primary']} no longer carries "
                f"{pair['cts_urn']}; not reclassified",
            )
            continue
        previous_role = data.get("passage_role") or "original"
        data["passage_role"] = LOT2_POLICY["passage_role"]
        data["citable_as_primary"] = False
        data["primary_node_id"] = pair["primary"]
        data["synthesis_of_urn"] = pair["cts_urn"]
        data["quote_coverage_of_primary"] = pair["quote_coverage"]
        data[f"{STAMP}_lot2"] = (
            f"English editorial synthesis quoting {pair['primary']} "
            f"({pair['quote_coverage']:.0%} of its text). It shared the primary's CTS URN "
            f"and role ({previous_role}), so it could be cited as if it were the ancient "
            "author. The URN is removed from cts_urn — which is the collision — and kept "
            "in synthesis_of_urn; the locus stays resolvable via primary_node_id."
        )
        data.pop("cts_urn", None)
        set_meta(synthesis, data)
        note(
            "lot2_classify",
            f"{pair['synthesis']} -> editorial_synthesis of {pair['primary']}",
        )

    # ==================================================================
    # LOT 3 — Tertullian reattributions
    # ==================================================================
    rename: dict[str, str] = {}
    for cluster in TERTULLIAN_REATTRIBUTIONS:
        home = cluster["real_work_node"]

        if cluster["create_work_node"] and home not in N:
            work = json.loads(json.dumps(TERTULLIAN_NEW_WORK_NODE))
            new_nodes.append(work)
            N[home] = work
            nodes.append(work)
            authorship = json.loads(json.dumps(TERTULLIAN_NEW_WORK_EDGE))
            if authorship["target"] not in N:
                warn(
                    "tert_create_work",
                    f"{authorship['target']} not found; no authorship edge",
                )
            elif (
                authorship["source"],
                authorship["relation"],
                authorship["target"],
            ) not in triples:
                new_edges.append(authorship)
                triples.add(
                    (authorship["source"], authorship["relation"], authorship["target"])
                )
            note("tert_create_work", f"{home}: {cluster['real_work']}")

        for n_ch in cluster["chapters"]:
            old_id = f"{cluster['id_prefix']}{n_ch}"
            new_id = f"{cluster['id_prefix_new']}{n_ch}"
            node = N.get(old_id) or N.get(new_id)
            if node is None:
                warn("tert_reattribute", f"{old_id} not found")
                continue
            if nid(node) == new_id and meta(node).get(STAMP):
                continue  # idempotent

            data = meta(node)
            data[f"{STAMP}_reattribution"] = (
                f"id and canonical_ref said {cluster['claimed_by_id']}; label said "
                f"{cluster['claimed_by_label']}. The text is {cluster['real_work']}. "
                f"{cluster['evidence']}"
            )
            data["work_attribution_evidence"] = cluster["certainty"]
            for key in TERTULLIAN_METADATA_KEYS["rewrite"]:
                if key == "canonical_ref":
                    data[key] = cluster["canonical_ref_fmt"].format(n=n_ch)
                elif key == "work_title":
                    data[key] = cluster["work_title"]
            for key in TERTULLIAN_METADATA_KEYS["clear"]:
                if key in data:
                    data[f"{key}_removed_by_{STAMP}"] = data[key]
                    data.pop(key)
            for flag, why in (cluster.get("flags") or {}).items():
                data[flag] = why
            data[STAMP] = "tert_reattribute"
            set_meta(node, data)
            node["label"] = cluster["label_fmt"].format(n=n_ch)

            if old_id != new_id:
                rename[old_id] = new_id
            note("tert_reattribute", f"{old_id} -> {new_id} ({cluster['real_work']})")

        # drop the false part_of edges; keep the true parent
        for wrong_home in cluster["drop_part_of"]:
            kids = [
                e
                for e in edges
                if e["relation"] == "part_of"
                and e["target"] == wrong_home
                and e["source"].startswith(
                    (cluster["id_prefix"], cluster["id_prefix_new"])
                )
            ]
            if not kids:
                continue
            kept = 0
            for e in kids:
                still_parented = any(
                    x["relation"] == "part_of"
                    and x["source"] == e["source"]
                    and x["target"] == home
                    and x["edge_id"] not in drop_edge_ids
                    for x in edges
                ) or home in {
                    n["target"] for n in new_edges if n["source"] == e["source"]
                }
                if still_parented:
                    drop_edge_ids.add(e["edge_id"])
                else:
                    # never orphan: re-point instead of deleting
                    triple = (e["source"], "part_of", home)
                    if triple in triples:
                        drop_edge_ids.add(e["edge_id"])
                    else:
                        triples.discard((e["source"], "part_of", e["target"]))
                        triples.add(triple)
                        e["target"] = e["target_id"] = home
                        stamp(
                            e,
                            "tert_repoint_part_of",
                            f"repointed from {wrong_home} to {home}: {cluster['evidence'][:180]}",
                        )
                        kept += 1
            note(
                "tert_drop_part_of",
                f"{wrong_home}: {len(kids) - kept} dropped, {kept} repointed to {home}",
            )

        for work_id, why in TERTULLIAN_EMPTIED_WORKS.items():
            node = N.get(work_id)
            if node is None:
                continue
            data = meta(node)
            if data.get(f"{STAMP}_emptied"):
                continue
            data["needs_text_ingestion"] = True
            data[f"{STAMP}_emptied"] = why
            set_meta(node, data)
            counts["tert_mark_emptied"] = counts.get("tert_mark_emptied", 0) + 1

    # ---- propagate the renames ----------------------------------------
    if rename:
        for node in nodes:
            if nid(node) in rename:
                new_id = rename[nid(node)]
                if "node_id" in node:
                    node["node_id"] = new_id
                if "id" in node:
                    node["id"] = new_id
        for edge in edges + new_edges:
            for field in ("source", "source_id", "target", "target_id"):
                if edge.get(field) in rename:
                    edge[field] = rename[edge[field]]
        blob = json.dumps(citations, ensure_ascii=False)
        for old_id, new_id in rename.items():
            blob = blob.replace(f'"{old_id}"', f'"{new_id}"')
        citations = json.loads(blob)
        # metadata pointers anywhere in the graph
        for node in nodes:
            data = meta(node)
            touched = False
            for key, value in list(data.items()):
                if isinstance(value, str) and value in rename:
                    data[key] = rename[value]
                    touched = True
            if touched:
                set_meta(node, data)
        note(
            "tert_rename_propagated",
            f"{len(rename)} ids renamed across nodes/edges/citations",
        )

    # ==================================================================
    # gate any node this wave creates, exactly as an ingestion would
    # ==================================================================
    if new_nodes or new_edges:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as fh:
            json.dump({"nodes": new_nodes, "edges": new_edges}, fh, ensure_ascii=False)
            gate_path = fh.name
        proc = subprocess.run(
            [sys.executable, str(RULES_CHECKER), "--new-only", gate_path],
            capture_output=True,
            text=True,
        )
        print("\n--- check_ingestion_rules.py --new-only (created records) ---")
        print(proc.stdout.strip() or "(no output)")
        Path(gate_path).unlink(missing_ok=True)
        if proc.returncode != 0:
            print(
                "REFUSING: the created records do not pass the gate.", file=sys.stderr
            )
            return 3

    # ==================================================================
    # invariants
    # ==================================================================
    edges = [e for e in edges if e.get("edge_id") not in drop_edge_ids] + new_edges

    ids = [nid(n) for n in nodes]
    assert len(ids) == len(set(ids)), "duplicate node ids"
    present = set(ids)
    dangling = [
        e for e in edges if e["source"] not in present or e["target"] not in present
    ]
    assert not dangling, f"dangling edges: {[e['edge_id'] for e in dangling][:5]}"
    unpaired = [
        e
        for e in edges
        if e["source"] != e["source_id"] or e["target"] != e["target_id"]
    ]
    assert not unpaired, (
        f"source/source_id or target/target_id disagree: {unpaired[:3]}"
    )
    triple_list = [(e["source"], e["relation"], e["target"]) for e in edges]
    assert len(triple_list) == len(set(triple_list)), "duplicate triples"
    assert not [e for e in edges if e["source"] == e["target"]], "self-loops"

    # every Tertullian passage keeps exactly one work parent
    for cluster in TERTULLIAN_REATTRIBUTIONS:
        for n_ch in cluster["chapters"]:
            pid = f"{cluster['id_prefix_new']}{n_ch}"
            if pid not in present:
                continue
            parents = [
                e["target"]
                for e in edges
                if e["relation"] == "part_of" and e["source"] == pid
            ]
            assert len(parents) == 1, f"{pid} has parents {parents}"
            assert parents[0] == cluster["real_work_node"], f"{pid} -> {parents[0]}"

    # no editorial synthesis still collides with its primary on the R2 key
    key_owner: dict[tuple, str] = {}
    for node in nodes:
        if node.get("type") != "passage":
            continue
        data = meta(node)
        if data.get("citable_as_primary") is False:
            assert not data.get("cts_urn"), f"{nid(node)} keeps a colliding cts_urn"
            assert data.get("primary_node_id") in present, (
                f"{nid(node)} primary dangles"
            )
        urn = data.get("cts_urn")
        if urn:
            key_owner.setdefault(
                (urn, data.get("passage_role") or "original"), nid(node)
            )

    # no dialectical edge left in the g5 batch without a verdict
    orphan_g5 = [
        e["edge_id"]
        for e in edges
        if e["relation"] in DIALECTICAL_RELATIONS
        and meta(e).get("provenance") == "g5_deep_2026_06_15"
        and not meta(e).get(STAMP)
    ]
    assert not orphan_g5, f"g5 dialectical edges with no verdict: {orphan_g5}"

    # ==================================================================
    # report
    # ==================================================================
    print(
        f"\nnodes {before[0]} -> {len(nodes)}   edges {before[1]} -> {len(edges)}   "
        f"citations {before[2]} -> {len(citations)}"
    )
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print("invariants: OK")
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for line in skipped:
            print("  " + line)

    if dry_run:
        print("\n--dry-run (default): nothing written. Use --write to apply.")
        return 0

    for path in (NODES_PATH, EDGES_PATH, CITATIONS_PATH):
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + BAK_SUFFIX))
    write_jsonl(NODES_PATH, nodes)
    write_jsonl(EDGES_PATH, edges)
    if CITATIONS_PATH.exists():
        write_jsonl(CITATIONS_PATH, citations)

    report = ROOT / "data" / "audit" / "2026-08-17_dialectical_repairs_applied.md"
    report.write_text(
        "# Dialectical layer and editorial syntheses (wave 6) — applied 2026-08-17\n\n"
        f"nodes {before[0]} -> {len(nodes)}, edges {before[1]} -> {len(edges)}, "
        f"citations {before[2]} -> {len(citations)}\n\n"
        + "\n".join(f"- {line}" for line in log)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"\nwrote {NODES_PATH}\nwrote {EDGES_PATH}\nwrote {CITATIONS_PATH}\nwrote {report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
