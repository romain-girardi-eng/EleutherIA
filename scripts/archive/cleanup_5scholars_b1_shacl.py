"""Cleanup 59 SHACL invariants introduced by the 5-scholars B1 batches
(Frede 2011 / Bobzien 2001 / Dihle 1982 / Destrée 2014 / Fürst 2022).

Strategy (per `knowledge graph/ontology/edge_types.json`):

  - synthesis|argument --discusses|part_of--> publication  : DROP
    (publication anchoring is metadata convention, see amand_b9 pattern)

  - argument --responds_to--> publication                  : REWRITE to critiques
    (`critiques` accepts argument→publication; `responds_to` does not)

  - person --wrote--> publication                          : REWRITE to
    publication --authored_by--> person  (valid direction)

  - {synthesis,argument} --authored_by--> {argument node typed as
    `scholar_position_*`}                                   : DROP
    (target should be a person; scholar position is an argument node, attribution
    is already in synthesis metadata)

  - {scholar_position_X (argument)} --influences--> person  : DROP
  - person --influences--> {scholar_position_X (argument)}  : DROP
    (use `critiques`/`responds_to` style on the argument node itself; influence
    edges require person/school/work endpoints)

  - publication --precedes--> publication                   : DROP
    (precedence is implicit via dates in metadata)

Idempotent: re-running drops nothing extra; produces an explicit log of changes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_PATH = REPO_ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = REPO_ROOT / "data" / "kg" / "edges.jsonl"
ONT_PATH = REPO_ROOT / "knowledge graph" / "ontology" / "edge_types.json"


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dump_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main() -> int:
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    node_type = {n["id"]: n.get("type") for n in nodes}
    print(f"Loaded {len(nodes):,} nodes, {len(edges):,} edges")

    dropped: list[tuple[str, str, str, str]] = []
    rewritten: list[tuple[str, str, str, str]] = []
    new_edges: list[dict] = []

    SCHOLAR_POSITION_PREFIX = "scholar_position_"

    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        rel = e.get("relation")
        s_t = node_type.get(src)
        t_t = node_type.get(tgt)

        # Rule 1: synthesis|argument --discusses|part_of--> publication  : DROP
        if (
            s_t in {"synthesis", "argument"}
            and rel in {"discusses", "part_of"}
            and t_t == "publication"
        ):
            dropped.append((src, rel, tgt, "rule1_drop_to_pub"))
            continue

        # Rule 2: argument --responds_to--> publication  : REWRITE -> critiques
        if s_t == "argument" and rel == "responds_to" and t_t == "publication":
            e2 = dict(e)
            e2["relation"] = "critiques"
            md = dict(e2.get("metadata") or {})
            md["original_relation"] = "responds_to"
            md["rewrite_reason"] = "responds_to does not accept publication target; semantic intent preserved via critiques"
            e2["metadata"] = md
            new_edges.append(e2)
            rewritten.append((src, rel, tgt, "rule2_rewrite_to_critiques"))
            continue

        # Rule 3: person --wrote--> publication  : REWRITE -> publication authored_by person
        if s_t == "person" and rel == "wrote" and t_t == "publication":
            e2 = {
                "source": tgt,
                "target": src,
                "relation": "authored_by",
                "confidence": e.get("confidence", 0.9),
            }
            md = dict(e.get("metadata") or {})
            md["original_edge"] = f"{src} --wrote--> {tgt}"
            md["rewrite_reason"] = "wrote requires work target; inverted to authored_by for publication"
            e2["metadata"] = md
            new_edges.append(e2)
            rewritten.append((src, rel, tgt, "rule3_invert_wrote"))
            continue

        # Rule 4: {synthesis,argument} --authored_by--> {argument node with scholar_position_ prefix}  : DROP
        if (
            s_t in {"synthesis", "argument"}
            and rel == "authored_by"
            and t_t == "argument"
            and isinstance(tgt, str)
            and tgt.startswith(SCHOLAR_POSITION_PREFIX)
        ):
            dropped.append((src, rel, tgt, "rule4_drop_authored_by_to_scholar_position"))
            continue

        # Rule 5: scholar_position_X (argument) --influences--> person  : DROP
        if (
            s_t == "argument"
            and isinstance(src, str)
            and src.startswith(SCHOLAR_POSITION_PREFIX)
            and rel == "influences"
            and t_t == "person"
        ):
            dropped.append((src, rel, tgt, "rule5_drop_scholar_position_influences"))
            continue

        # Rule 6: person --influences--> scholar_position_X (argument)  : DROP
        if (
            s_t == "person"
            and rel == "influences"
            and t_t == "argument"
            and isinstance(tgt, str)
            and tgt.startswith(SCHOLAR_POSITION_PREFIX)
        ):
            dropped.append((src, rel, tgt, "rule6_drop_influences_to_scholar_position"))
            continue

        # Rule 7: publication --precedes--> publication  : DROP
        if s_t == "publication" and rel == "precedes" and t_t == "publication":
            dropped.append((src, rel, tgt, "rule7_drop_pub_precedes_pub"))
            continue

        new_edges.append(e)

    print(f"\nDROPPED: {len(dropped)} edges")
    for src, rel, tgt, reason in dropped[:5]:
        print(f"  [{reason}] {src} --{rel}--> {tgt}")
    if len(dropped) > 5:
        print(f"  ... ({len(dropped) - 5} more)")

    print(f"\nREWRITTEN: {len(rewritten)} edges")
    for src, rel, tgt, reason in rewritten:
        print(f"  [{reason}] {src} --{rel}--> {tgt}")

    print(f"\nFinal: {len(new_edges):,} edges (was {len(edges):,}; delta {len(new_edges) - len(edges):+d})")
    dump_jsonl(EDGES_PATH, new_edges)
    print(f"Wrote {EDGES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
