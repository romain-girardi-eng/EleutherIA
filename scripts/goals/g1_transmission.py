#!/usr/bin/env python3
"""G1 — Transmission / influence-chain analysis over the EleutherIA KG.

Strictly READ-ONLY on the KG (data/kg/nodes.jsonl, data/kg/edges.jsonl).
No node or edge is ever written back.

Builds a *directed* person-person influence graph from the dialectical
relations that carry a forward-in-time / influence direction:

    influences, student_of, teaches, precedes, responds_to

(plus their inverses, normalized to a single forward direction A --rel--> B,
meaning "A is upstream of / influences B").

It then provides:

  1. transmission_path(A, B): the shortest labeled edge chain from person A to
     person B in that directed graph. For each hop A_i -> A_{i+1} it attaches a
     *licensing passage*: a primary-text passage_id (or a parallel_to /
     shared-grounded-argument edge) that grounds the dialectical link, so the
     chain is not a bare assertion but is anchored in the corpus.

  2. Betweenness centrality over the directed person graph -> the brokers of
     transmission (who sits on the most shortest paths).

  3. The worklist of isolated persons: persons with NO person-person
     dialectical edge (in or out) in the directed relation set.

Licensing model (how a hop A -> B is grounded in a passage):
  Priority order, first hit wins:
    L1 shared_argument  : an argument node X with a person-link to BOTH A and B
                          (created_by / creates / authored_by / discusses /
                          interprets / critiques ...), AND X cites_primary_source
                          to a passage -> that passage_id licenses the hop.
    L2 cites_about      : an argument X person-linked to B (the receiver) that
                          cites_primary_source a passage authored_by A (the
                          source) -> B's argument quotes A's text.
    L3 parallel_to      : a parallel_to edge between a passage/concept of A and a
                          passage/concept of B (verbatim / thematic overlap).
    L4 shared_argument_nopass : an argument node linked to both A and B but with
                          no cited passage (records the argument_id as licence).
    L5 none             : no licence found in the KG (hop is asserted only by the
                          dialectical edge itself; flagged honestly).

Modern labels (libertarian / compatibilism / "invention of the will") are never
asserted here; this script only reports graph structure and passage anchors.

Usage:
    python3 scripts/goals/g1_transmission.py            # run canonical battery
    python3 scripts/goals/g1_transmission.py --path A B  # one path by id-substr
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Coarse chronological ordering by period, used only to orient the *augmented*
# (shared-argument / parallel_to) transmission edges forward in time. The
# primary directed-influence edges never use this.
PERIOD_ORDER = {
    "Presocratic": 0, "Archaic": 0, "Classical": 1, "Classical Greek": 1,
    "Second Temple Judaism": 2, "Hellenistic": 2, "Roman Republican": 3,
    "Roman Imperial": 4, "Imperial": 4, "Roman": 4, "Middle Platonism": 4,
    "Patristic": 5, "Late Antiquity": 6, "Byzantine": 7, "Medieval": 8,
    "Renaissance": 9, "Early Modern": 10, "Modern": 11, "Contemporary": 12,
}


def person_year(pid: str) -> int | None:
    """Best-effort sortable year from a person id (negative = BCE)."""
    m = re.search(r"_(\d{3,4})_(\d{3,4})(bce|ce)", pid)
    if m:
        return -int(m.group(1)) if m.group(3) == "bce" else int(m.group(1))
    m = re.search(r"_d(\d{3,4})", pid)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{3,4})bce", pid)
    if m:
        return -int(m.group(1))
    m = re.search(r"_(\d{3,4})ce", pid)
    if m:
        return int(m.group(1))
    return None

ROOT = Path(__file__).resolve().parents[2]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
OUT_DIR = ROOT / "data" / "goals" / "g1"

# Directed person-person relations interpreted as forward influence A -> B.
# Each entry maps a raw relation to ("forward"|"reverse"): forward keeps the
# edge as source->target = upstream->downstream; reverse flips it.
DIRECTED_FORWARD = {
    "influences": "forward",      # A influences B
    "teaches": "forward",         # A teaches B
    "precedes": "forward",        # A precedes B (chronological/doctrinal)
    "student_of": "reverse",      # A student_of B  =>  B -> A
    "responds_to": "reverse",     # A responds_to B =>  B precedes/seeds A
    "influenced_by": "reverse",   # A influenced_by B => B -> A
}

# Relations connecting an argument node to a person node (either direction).
ARG_PERSON_RELS = {
    "created_by", "creates", "authored_by", "discusses", "interprets",
    "critiques", "supports", "develops", "developed_by", "extends",
    "employs", "responds_to", "influences", "opposes", "engages_with",
}


@dataclass
class KG:
    persons: dict[str, str] = field(default_factory=dict)       # id -> label
    node_type: dict[str, str] = field(default_factory=dict)     # id -> type
    period: dict[str, str] = field(default_factory=dict)        # id -> period
    # directed person graph: adj[A] = {B: relation}
    adj: dict[str, dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    radj: dict[str, dict[str, str]] = field(default_factory=lambda: defaultdict(dict))
    # licensing indices
    arg_persons: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))   # arg -> {persons}
    person_args: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))   # person -> {args}
    arg_passages: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # arg -> {passages}
    person_passages: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # person -> {passages they authored}
    person_units: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # person -> {passages+concepts attributable}
    parallels: list[tuple[str, str, str]] = field(default_factory=list)  # (a, b, theme)


def load_kg() -> KG:
    kg = KG()
    with NODES_PATH.open() as f:
        for line in f:
            n = json.loads(line)
            nid, ntype = n.get("id"), n.get("type")
            kg.node_type[nid] = ntype
            if ntype == "person":
                kg.persons[nid] = n.get("label") or nid
                kg.period[nid] = n.get("period") or ""

    persons = set(kg.persons)
    with EDGES_PATH.open() as f:
        for line in f:
            e = json.loads(line)
            s, t, r = e.get("source"), e.get("target"), e.get("relation")
            if s is None or t is None:
                continue

            # 1) directed person-person influence graph
            if r in DIRECTED_FORWARD and s in persons and t in persons:
                a, b = (s, t) if DIRECTED_FORWARD[r] == "forward" else (t, s)
                if a != b and b not in kg.adj[a]:
                    # store a forward-reading relation label so reversed edges
                    # (student_of, influenced_by, responds_to) don't display
                    # anachronistically as "X influenced_by Y" with X upstream
                    fwd = {"student_of": "teaches", "influenced_by": "influences",
                           "responds_to": "precedes"}.get(r, r) if DIRECTED_FORWARD[r] == "reverse" else r
                    kg.adj[a][b] = fwd
                    kg.radj[b][a] = fwd

            # 2) argument <-> person links (for licensing)
            if r in ARG_PERSON_RELS:
                a_is_arg = kg.node_type.get(s) == "argument" and t in persons
                b_is_arg = kg.node_type.get(t) == "argument" and s in persons
                if a_is_arg:
                    kg.arg_persons[s].add(t)
                    kg.person_args[t].add(s)
                if b_is_arg:
                    kg.arg_persons[t].add(s)
                    kg.person_args[s].add(t)

            # 3) argument -> passage (cites_primary_source etc.)
            if r in ("cites_primary_source", "evidenced_by", "grounded_in", "cites"):
                if kg.node_type.get(s) == "argument" and t.startswith("passage_"):
                    kg.arg_passages[s].add(t)
                if kg.node_type.get(t) == "argument" and s.startswith("passage_"):
                    kg.arg_passages[t].add(s)

            # 4) passage authored_by person
            if r == "authored_by" and s.startswith("passage_") and t in persons:
                kg.person_passages[t].add(s)
                kg.person_units[t].add(s)

            # 5) parallel_to verbatim/thematic overlap (passages or concepts)
            if r == "parallel_to":
                theme = ""
                md = e.get("metadata")
                if isinstance(md, str):
                    try:
                        theme = json.loads(md).get("theme", "")
                    except Exception:
                        theme = ""
                kg.parallels.append((s, t, theme))

    # attribute concepts/passages to persons via their authored arguments
    for arg, ppl in kg.arg_persons.items():
        for p in ppl:
            kg.person_units[p].update(kg.arg_passages.get(arg, set()))

    return kg


def _order(kg: KG, a: str, b: str) -> tuple[str, str] | None:
    """Orient an augmented edge forward in time (returns (earlier, later))."""
    ya, yb = person_year(a), person_year(b)
    if ya is not None and yb is not None and ya != yb:
        return (a, b) if ya < yb else (b, a)
    pa = PERIOD_ORDER.get(kg.period.get(a, ""))
    pb = PERIOD_ORDER.get(kg.period.get(b, ""))
    if pa is not None and pb is not None and pa != pb:
        return (a, b) if pa < pb else (b, a)
    return None  # cannot orient -> skip (avoid anachronistic chains)


def build_augmented(kg: KG) -> dict[str, dict[str, dict[str, Any]]]:
    """Augmented directed transmission graph = directed influence edges PLUS
    time-oriented shared-grounded-argument and parallel_to edges.

    Edge value carries the licence so paths through this layer stay grounded.
    """
    aug: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    # tier 1: the strict directed influence edges (authoritative)
    for a, nbrs in kg.adj.items():
        for b, rel in nbrs.items():
            aug[a][b] = {"relation": rel, "tier": "influence"}

    # tier 2: shared grounded argument -> two persons co-author the same argument
    for arg, ppl in kg.arg_persons.items():
        pl = sorted(ppl)
        for i in range(len(pl)):
            for j in range(i + 1, len(pl)):
                o = _order(kg, pl[i], pl[j])
                if not o:
                    continue
                a, b = o
                if b not in aug[a]:  # don't overwrite an influence edge
                    aug[a][b] = {"relation": "shared_argument", "tier": "argument",
                                 "argument_id": arg}

    # tier 3: parallel_to between persons' units (passages/concepts)
    unit_owner: dict[str, set[str]] = defaultdict(set)
    for p, units in kg.person_units.items():
        for u in units:
            unit_owner[u].add(p)
    for s, t, theme in kg.parallels:
        for pa in unit_owner.get(s, set()):
            for pb in unit_owner.get(t, set()):
                if pa == pb:
                    continue
                o = _order(kg, pa, pb)
                if not o:
                    continue
                a, b = o
                if b not in aug[a]:
                    aug[a][b] = {"relation": "parallel_to", "tier": "parallel",
                                 "passage_id": s, "parallel_target": t,
                                 "theme": theme}
    return aug


def license_hop(kg: KG, a: str, b: str) -> dict[str, Any]:
    """Find a passage (or parallel/argument) that grounds the hop a -> b."""
    args_a, args_b = kg.person_args.get(a, set()), kg.person_args.get(b, set())

    # L1: shared argument with a cited passage
    shared = args_a & args_b
    for arg in sorted(shared):
        passes = kg.arg_passages.get(arg, set())
        if passes:
            return {"licence_type": "shared_argument", "argument_id": arg,
                    "passage_id": sorted(passes)[0],
                    "all_passages": sorted(passes)}

    # L2: an argument of B (receiver) that cites a passage authored by A (source)
    a_pass = kg.person_passages.get(a, set())
    if a_pass:
        for arg in sorted(args_b):
            cited = kg.arg_passages.get(arg, set()) & a_pass
            if cited:
                return {"licence_type": "cites_source_text", "argument_id": arg,
                        "passage_id": sorted(cited)[0], "all_passages": sorted(cited)}
    # symmetric: argument of A citing passage of B
    b_pass = kg.person_passages.get(b, set())
    if b_pass:
        for arg in sorted(args_a):
            cited = kg.arg_passages.get(arg, set()) & b_pass
            if cited:
                return {"licence_type": "cites_source_text", "argument_id": arg,
                        "passage_id": sorted(cited)[0], "all_passages": sorted(cited)}

    # L3: parallel_to between a unit (passage/concept) of A and a unit of B
    units_a, units_b = kg.person_units.get(a, set()), kg.person_units.get(b, set())
    for s, t, theme in kg.parallels:
        if (s in units_a and t in units_b) or (s in units_b and t in units_a):
            return {"licence_type": "parallel_to", "passage_id": s,
                    "parallel_target": t, "theme": theme}

    # L4: shared argument without a cited passage. Distinguish a primary-text
    # argument from a secondary-literature (scholarly_*) reception node so we
    # never present modern reception as if it were a primary passage.
    if shared:
        arg = sorted(shared)[0]
        scholarly = arg.startswith(("scholarly_argument_", "scholar_")) or "_20" in arg
        return {"licence_type": "scholarly_reception" if scholarly else "shared_argument_nopass",
                "argument_id": arg, "passage_id": None}

    # L5: nothing grounds it beyond the dialectical edge itself
    return {"licence_type": "none", "passage_id": None}


def _bfs(adj: dict[str, dict[str, Any]], a: str, b: str) -> list[str] | None:
    prev: dict[str, str | None] = {a: None}
    q = deque([a])
    while q:
        cur = q.popleft()
        if cur == b:
            break
        for nxt in adj.get(cur, {}):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    if b not in prev:
        return None
    chain, cur = [], b
    while cur is not None:
        chain.append(cur)
        cur = prev[cur]
    chain.reverse()
    return chain


def transmission_path(kg: KG, a: str, b: str,
                      aug: dict[str, dict[str, dict[str, Any]]] | None = None) -> dict[str, Any]:
    """Shortest labeled directed edge chain a -> b, with per-hop licensing.

    First tries the strict directed-influence graph. If no chain exists and an
    augmented graph is supplied, falls back to it (shared-argument / parallel_to
    transmission edges, oriented forward in time).
    """
    if a not in kg.persons or b not in kg.persons:
        return {"found": False,
                "error": f"unknown person: {a if a not in kg.persons else b}"}
    if a == b:
        return {"found": True, "hops": [], "node_chain": [a], "graph": "trivial"}

    graph_used = "influence"
    chain = _bfs(kg.adj, a, b)
    if chain is None and aug is not None:
        chain = _bfs(aug, a, b)
        graph_used = "augmented"
    if chain is None:
        return {"found": False, "source": a, "target": b,
                "source_label": kg.persons[a], "target_label": kg.persons[b],
                "reason": "no directed dialectical path "
                          "(influence graph; no augmented chain)"}

    edge_src = kg.adj if graph_used == "influence" else aug
    hops = []
    for i in range(len(chain) - 1):
        x, y = chain[i], chain[i + 1]
        meta = edge_src[x][y]  # type: ignore[index]
        rel = meta if isinstance(meta, str) else meta["relation"]
        lic = license_hop(kg, x, y)
        # if the augmented edge already carries a licence and license_hop found
        # nothing stronger, surface the augmented edge's own grounding
        if isinstance(meta, dict) and lic["licence_type"] in ("none", "shared_argument_nopass", "scholarly_reception"):
            if meta.get("tier") == "argument":
                arg_id = meta["argument_id"]
                shared_pass = kg.arg_passages.get(arg_id, set())
                if shared_pass:
                    lic = {"licence_type": "shared_argument", "argument_id": arg_id,
                           "passage_id": sorted(shared_pass)[0],
                           "all_passages": sorted(shared_pass)}
                else:
                    scholarly = arg_id.startswith(("scholarly_argument_", "scholar_")) or "_20" in arg_id
                    lic = {"licence_type": "scholarly_reception" if scholarly else "shared_argument_nopass",
                           "argument_id": arg_id, "passage_id": None}
            elif meta.get("tier") == "parallel":
                lic = {"licence_type": "parallel_to", "passage_id": meta["passage_id"],
                       "parallel_target": meta["parallel_target"], "theme": meta.get("theme", "")}
        hops.append({
            "from": x, "from_label": kg.persons[x],
            "to": y, "to_label": kg.persons[y],
            "relation": rel,
            "tier": meta.get("tier", "influence") if isinstance(meta, dict) else "influence",
            "licence": lic,
        })
    return {"found": True, "source": a, "target": b,
            "source_label": kg.persons[a], "target_label": kg.persons[b],
            "length": len(hops), "graph": graph_used,
            "node_chain": chain, "hops": hops}


def betweenness(kg: KG) -> list[tuple[str, float]]:
    """Brandes betweenness centrality on the directed person graph."""
    nodes = [p for p in kg.persons if kg.adj.get(p) or kg.radj.get(p)]
    cb = dict.fromkeys(nodes, 0.0)
    nodeset = set(nodes)
    for s in nodes:
        stack, pred = [], defaultdict(list)
        sigma = dict.fromkeys(nodeset, 0.0); sigma[s] = 1.0
        dist = {s: 0}
        q = deque([s])
        while q:
            v = q.popleft(); stack.append(v)
            for w in kg.adj.get(v, {}):
                if w not in nodeset:
                    continue
                if w not in dist:
                    dist[w] = dist[v] + 1; q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]; pred[w].append(v)
        delta = dict.fromkeys(nodeset, 0.0)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                if sigma[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    return sorted(cb.items(), key=lambda kv: kv[1], reverse=True)


def isolated_persons(kg: KG) -> list[str]:
    """Persons with NO person-person dialectical edge (in or out)."""
    return sorted(p for p in kg.persons if not kg.adj.get(p) and not kg.radj.get(p))


def resolve(kg: KG, substr: str) -> str:
    if substr in kg.persons:
        return substr
    hits = [p for p in kg.persons if substr.lower() in p.lower()
            or substr.lower() in kg.persons[p].lower()]
    if not hits:
        raise SystemExit(f"no person matches {substr!r}")
    return sorted(hits, key=len)[0]


CANONICAL = [
    ("carneades", "boethius"),
    ("carneades", "origen"),
    ("alexander_aphrodisias", "origen"),
    ("chrysippus", "augustine"),
]


def fmt_hop(h: dict[str, Any]) -> str:
    lic = h["licence"]
    lt = lic["licence_type"]
    pid = lic.get("passage_id")
    if lt == "shared_argument":
        tag = f"licensed by {pid} (shared argument {lic['argument_id']})"
    elif lt == "cites_source_text":
        tag = f"licensed by {pid} (argument {lic['argument_id']} cites source text)"
    elif lt == "parallel_to":
        tag = f"licensed by parallel_to {pid} || {lic['parallel_target']}" + (f" [{lic['theme']}]" if lic.get("theme") else "")
    elif lt == "shared_argument_nopass":
        tag = f"licensed by shared argument {lic['argument_id']} (no cited passage)"
    elif lt == "scholarly_reception":
        tag = f"attested by scholarly-reception node {lic['argument_id']} (secondary lit, no primary passage)"
    else:
        tag = "NO passage licence (dialectical edge only)"
    return (f"  {h['from_label']} --{h['relation']}--> {h['to_label']}\n"
            f"      {tag}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", nargs=2, metavar=("A", "B"))
    args = ap.parse_args()

    kg = load_kg()
    aug = build_augmented(kg)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    n_persons = len(kg.persons)
    connected = {p for p in kg.persons if kg.adj.get(p) or kg.radj.get(p)}
    iso = isolated_persons(kg)
    iso_ancient = [p for p in iso
                   if not p.startswith("scholar_") and "contemporary" not in p]
    iso_scholar = [p for p in iso if p not in set(iso_ancient)]
    bw = betweenness(kg)

    if args.path:
        a, b = resolve(kg, args.path[0]), resolve(kg, args.path[1])
        res = transmission_path(kg, a, b, aug)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    # canonical battery
    results = {}
    for sa, sb in CANONICAL:
        a, b = resolve(kg, sa), resolve(kg, sb)
        results[f"{sa}__to__{sb}"] = transmission_path(kg, a, b, aug)

    payload = {
        "stats": {
            "total_persons": n_persons,
            "connected_persons": len(connected),
            "isolated_persons": len(iso),
            "isolated_ancient": len(iso_ancient),
            "isolated_scholar": len(iso_scholar),
            "directed_edges": sum(len(v) for v in kg.adj.values()),
        },
        "top_betweenness": [
            {"id": pid, "label": kg.persons[pid], "betweenness": round(v, 3)}
            for pid, v in bw[:10]
        ],
        "isolated_worklist": [{"id": p, "label": kg.persons[p]} for p in iso],
        "paths": results,
    }
    (OUT_DIR / "transmission_paths.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2))

    # markdown report
    md = ["# G1 — Transmission / Influence Chains", "",
          "Directed person-person influence graph built from "
          "`influences, teaches, precedes, student_of, responds_to, influenced_by`.",
          "Each hop is anchored by a *licensing passage* (shared grounded argument, "
          "an argument citing the source's own text, or a `parallel_to` overlap). "
          "Modern labels are not asserted here.", "",
          "## Graph stats", "",
          f"- Persons: **{n_persons}**",
          f"- In the dialectical component (>=1 person-person edge): **{len(connected)}**",
          f"- Isolated persons (no dialectical edge): **{len(iso)}**",
          f"- Directed person-person edges: **{payload['stats']['directed_edges']}**",
          "", "## Top-10 betweenness (transmission brokers)", ""]
    for i, row in enumerate(payload["top_betweenness"], 1):
        md.append(f"{i}. **{row['label']}** — {row['betweenness']}  `{row['id']}`")
    md += ["", "## Canonical transmission paths", ""]
    for key, res in results.items():
        md.append(f"### {key.replace('__to__', ' → ')}")
        if not res.get("found"):
            md.append(f"_No directed dialectical path found "
                      f"({res.get('reason', res.get('error', ''))})._\n")
            continue
        gtag = ("strict influence graph" if res.get("graph") == "influence"
                else "augmented graph (shared-argument / parallel_to backbone)")
        md.append(f"**{res['source_label']} → {res['target_label']}** "
                  f"— {res['length']} hop(s) · _via {gtag}_\n")
        for h in res["hops"]:
            lic = h["licence"]
            md.append(f"- `{h['from_label']}` **--{h['relation']}-->** `{h['to_label']}`")
            lt = lic["licence_type"]
            if lt == "none":
                md.append("  - licence: _none — dialectical edge only_")
            elif lt == "parallel_to":
                md.append(f"  - licence: `parallel_to` {lic['passage_id']} ‖ "
                          f"{lic['parallel_target']}" +
                          (f" — _{lic['theme']}_" if lic.get("theme") else ""))
            elif lt == "shared_argument_nopass":
                md.append(f"  - licence: shared argument `{lic['argument_id']}` "
                          f"(no cited passage)")
            elif lt == "scholarly_reception":
                md.append(f"  - licence: _scholarly-reception node_ "
                          f"`{lic['argument_id']}` (secondary literature; "
                          f"no primary passage)")
            elif lt == "shared_argument":
                md.append(f"  - licence: passage **{lic['passage_id']}** "
                          f"via shared argument `{lic['argument_id']}`")
            else:
                md.append(f"  - licence: passage **{lic['passage_id']}** "
                          f"— argument `{lic['argument_id']}` cites source text")
        md.append("")
    md += ["## Isolated persons worklist "
           f"({len(iso)} — no person-person dialectical edge)",
           f"_{len(iso_ancient)} ancient/non-scholar (priority for wiring) · "
           f"{len(iso_scholar)} modern scholars._", "",
           "### Ancient / non-scholar (priority)", ""]
    anc = set(iso_ancient)
    for row in payload["isolated_worklist"]:
        if row["id"] in anc:
            md.append(f"- {row['label']}  `{row['id']}`")
    md += ["", "### Modern scholars", ""]
    for row in payload["isolated_worklist"]:
        if row["id"] not in anc:
            md.append(f"- {row['label']}  `{row['id']}`")
    (OUT_DIR / "transmission.md").write_text("\n".join(md) + "\n")

    # console summary
    print(f"persons={n_persons} connected={len(connected)} isolated={len(iso)} "
          f"directed_edges={payload['stats']['directed_edges']}")
    print("\nTop-10 betweenness:")
    for i, row in enumerate(payload["top_betweenness"], 1):
        print(f"  {i:2d}. {row['betweenness']:7.2f}  {row['label']}")
    for key, res in results.items():
        print(f"\n=== {key.replace('__to__', ' -> ')} ===")
        if not res.get("found"):
            print(f"  NO PATH: {res.get('reason', res.get('error',''))}")
            continue
        print(f"  {res['source_label']} -> {res['target_label']} "
              f"({res['length']} hops, via {res.get('graph')} graph)")
        for h in res["hops"]:
            print(fmt_hop(h))
    print(f"\nwrote {OUT_DIR/'transmission.md'} and "
          f"{OUT_DIR/'transmission_paths.json'}")


if __name__ == "__main__":
    main()
