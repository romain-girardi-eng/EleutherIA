"""Amand 1945 B5 — Origène (Livre II Ch. V, p. 275-325).

Témoin n°1 patristique d'Amand pour la lignée carnéadienne. Le chapitre le plus long du livre
(~50 pages, ll. 14740-17120 du .md OCR). Cible 33 inserts + 3 updates = 36 opérations,
~70 edges. Pattern Option B (audit + extraction + consolidation).

CRITIQUE : Origène a 414 passages SC132 (Contra Celsum livres I-II) + 8 SC268 (Princ. III.1, IV.1-3)
disponibles dans le KG. **Ancrage direct possible** via evidenced_by sur les §II sub-args (Princ. III.1)
et un sub-arg §III (Phil. 23.12-13 = excerpt CC II.20). Le reste (Phil. 23, Comm. Gen., Comm. Rom., CC III-VIII)
est evidence_pending.

Idempotent : déjà-faits skip. NE COMMIT PAS.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

KG_ROOT = Path(__file__).resolve().parent.parent / "data" / "kg"
NODES_PATH = KG_ROOT / "nodes.jsonl"
EDGES_PATH = KG_ROOT / "edges.jsonl"


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from amand_b5_utils import TIMESTAMP  # type: ignore
    from amand_b5_data import REPAIRS, UPDATES  # type: ignore
    from amand_b5_inserts import NEW_INSERTS  # type: ignore
    from amand_b5_edges import NEW_EDGES  # type: ignore

    print("== Loading current KG ==")
    nodes = [json.loads(line) for line in NODES_PATH.read_text().splitlines() if line.strip()]
    edges = [json.loads(line) for line in EDGES_PATH.read_text().splitlines() if line.strip()]
    print(f"  Nodes loaded: {len(nodes)}")
    print(f"  Edges loaded: {len(edges)}")

    node_by_id = {n["id"]: i for i, n in enumerate(nodes)}
    edge_by_id = {e.get("edge_id", e.get("id", "")): i for i, e in enumerate(edges)}

    # 1) Repairs (empty in B5)
    print("\n== REPAIR PHASE ==")
    repaired = 0
    for nid, repair in REPAIRS.items():
        if nid not in node_by_id:
            print(f"  MISSING (skip): {nid}")
            continue
        n = nodes[node_by_id[nid]]
        n["period"] = repair["period"]
        n["school"] = repair["school"]
        n["metadata"] = json.dumps(repair["md"], ensure_ascii=False)
        n["updated_at"] = TIMESTAMP
        if not isinstance(n.get("alternative_names"), str):
            n["alternative_names"] = json.dumps(n.get("alternative_names") or [])
        repaired += 1
    print(f"  Repaired: {repaired}")

    # 2) Updates
    print("\n== UPDATE PHASE ==")
    updated = 0
    skip_update_already = 0
    for nid, upd in UPDATES.items():
        if nid not in node_by_id:
            print(f"  MISSING (skip): {nid}")
            continue
        n = nodes[node_by_id[nid]]
        md_raw = n.get("metadata", "{}")
        existing_md = md_raw if isinstance(md_raw, dict) else json.loads(md_raw or "{}")
        # Idempotence : skip if wave already applied
        if existing_md.get("amand_b5_wave_applied"):
            print(f"  SKIP already-applied (wave): {nid}")
            skip_update_already += 1
            continue
        existing_md.update(upd["md_additions"])
        existing_md["amand_b5_wave_applied"] = True
        n["metadata"] = json.dumps(existing_md, ensure_ascii=False)
        if upd.get("description_append"):
            n["description"] = (n.get("description") or "") + "\n\n" + upd["description_append"]
        if upd.get("description_en_append"):
            n["description_en"] = (n.get("description_en") or "") + "\n\n" + upd["description_en_append"]
        n["updated_at"] = TIMESTAMP
        if not isinstance(n.get("alternative_names"), str):
            n["alternative_names"] = json.dumps(n.get("alternative_names") or [])
        updated += 1
    print(f"  Updated: {updated} ; skipped (already-applied): {skip_update_already}")

    # 3) Inserts
    print("\n== INSERT PHASE ==")
    inserted = 0
    skip_exists = 0
    for ins in NEW_INSERTS:
        if ins["id"] in node_by_id:
            skip_exists += 1
            continue
        nodes.append(ins)
        node_by_id[ins["id"]] = len(nodes) - 1
        inserted += 1
    print(f"  Inserted: {inserted} ; skipped (exists): {skip_exists}")

    # 4) Edges
    print("\n== EDGE PHASE ==")
    edge_inserted = 0
    edge_dup = 0
    edge_missing = 0
    for e in NEW_EDGES:
        eid = e["edge_id"]
        if eid in edge_by_id:
            edge_dup += 1
            continue
        if e["source"] not in node_by_id:
            print(f"  SKIP src missing: {e['source']} -> {e['target']} ({e['relation']})")
            edge_missing += 1
            continue
        if e["target"] not in node_by_id:
            print(f"  SKIP tgt missing: {e['source']} -> {e['target']} ({e['relation']})")
            edge_missing += 1
            continue
        edges.append(e)
        edge_by_id[eid] = len(edges) - 1
        edge_inserted += 1
    print(f"  Edges inserted: {edge_inserted} ; dup-skipped: {edge_dup} ; missing-skipped: {edge_missing}")

    # 5) Write back
    print("\n== WRITING BACK ==")
    with NODES_PATH.open("w") as f:
        for n in nodes:
            f.write(json.dumps(n, ensure_ascii=False) + "\n")
    with EDGES_PATH.open("w") as f:
        for ed in edges:
            f.write(json.dumps(ed, ensure_ascii=False) + "\n")
    print(f"  nodes.jsonl: {len(nodes)} ; edges.jsonl: {len(edges)}")
    print("\n== B5 CONSOLIDATION COMPLETE ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
