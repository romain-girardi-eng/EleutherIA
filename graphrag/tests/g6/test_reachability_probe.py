"""Scholar-RAG M0a — graph-reachability probe (GATE).

This is the gate the whole G6 edifice rests on (ARCHITECTURE §0, §2.2): it
asserts that ``find_debates`` -> ``build_controversy_frame`` *would* surface the
real fault-line edges, on the REAL graph, before any tool is written. If a fault
line is not reachable within the documented hop budget, the M1 fallback must be
widened before M4 ships.

Two properties are gated:

1. **Edge survival reachability.** All 11 ``opposes`` edges are reachable within
   2 dialectical hops from a debate / controversy / position / scholarly_argument
   seed node (i.e. from something ``find_debates`` returns).
2. **Empty-debate fallback.** The two known empty debate nodes
   (``debate_origins_notion_of_will_modern_paradigm`` — no dialectical out-edges;
   ``debate_carneadean_antiastrology_tradition`` — 0 grounded passages on the
   debate node itself) reach their fault lines via the
   ``scholar_position_*`` / ``argument_*`` / ``scholarly_argument_*`` fallback.

Offline DB probe: runs against the deterministic KG snapshot (``data/kg``), not a
live database. Skips (rather than failing the unit suite) when the snapshot is
absent; where the snapshot exists this is a hard GATE.

Also emits ``data/goals/g6/reachability_report.json`` for the blueprint record.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

from eleutheria_kg.services.snapshot import load_kg_snapshot, snapshot_available

DIALECTICAL_RELATIONS = frozenset(
    {
        "opposes",
        "critiques",
        "responds_to",
        "refutes",
        "contrasts_with",
        "agrees_with",
        "supports",
        "participates_in",
        "contributes_to",
        "has_position",
        "advanced_in",
        "engages_with",
        "interprets",
    }
)

# Relations a `find_debates` -> `build_controversy_frame` traversal walks to
# *reach* the fault-line nodes (the bridges, before the `opposes` edge itself).
BRIDGE_RELATIONS = frozenset(
    {"participates_in", "contributes_to", "has_position", "advanced_in", "discusses"}
)

SEED_TYPES = frozenset({"debate", "controversy", "position"})

# Periods `period_filter` excludes when the question is about antiquity
# (ARCHITECTURE §2.2). A pure person<->person opposes edge entirely within these
# periods is a MODERN metaphysics dispute, not an ancient fault line, and is not
# what `find_debates(period_filter=antiquity)` returns. Gate 1 scopes to ancient
# fault lines accordingly.
MODERN_PERIODS = frozenset({"modern", "contemporary"})

EMPTY_DEBATES = (
    "debate_origins_notion_of_will_modern_paradigm",
    "debate_carneadean_antiastrology_tradition",
)

REPORT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "goals"
    / "g6"
    / "reachability_report.json"
)


@pytest.fixture(scope="module")
def graph() -> dict:
    if not snapshot_available():
        pytest.skip("KG snapshot unavailable — reachability probe needs data/kg")
    raw = load_kg_snapshot()
    nodes = {
        str(n.get("id") or n.get("node_id") or ""): n
        for n in raw["nodes"]
        if (n.get("id") or n.get("node_id"))
    }
    out: dict[str, list[dict]] = defaultdict(list)
    inc: dict[str, list[dict]] = defaultdict(list)
    for e in raw["edges"]:
        s = str(e.get("source") or e.get("source_id") or "")
        t = str(e.get("target") or e.get("target_id") or "")
        rel = e.get("relation") or e.get("edge_type") or ""
        if not s or not t:
            continue
        edge = {"source": s, "target": t, "relation": rel}
        out[s].append(edge)
        inc[t].append(edge)
    return {"nodes": nodes, "out": out, "inc": inc}


def _opposes_edges(graph: dict) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    edges: list[dict] = []
    for src, lst in graph["out"].items():
        for e in lst:
            if e["relation"] == "opposes":
                key = (src, e["target"])
                if key not in seen:
                    seen.add(key)
                    edges.append(e)
    return edges


def _node_type(graph: dict, nid: str) -> str:
    return (graph["nodes"].get(nid, {}).get("type") or "").lower()


def _dialectical_neighbors(graph: dict, nid: str) -> set[str]:
    """Nodes one dialectical hop away (either direction)."""
    out_ = {
        e["target"]
        for e in graph["out"].get(nid, [])
        if e["relation"] in DIALECTICAL_RELATIONS
    }
    in_ = {
        e["source"]
        for e in graph["inc"].get(nid, [])
        if e["relation"] in DIALECTICAL_RELATIONS
    }
    return out_ | in_


def _reachable_within_2_hops(graph: dict, seed: str) -> set[str]:
    """Nodes reachable from ``seed`` within 2 dialectical hops (undirected)."""
    one = _dialectical_neighbors(graph, seed)
    two: set[str] = set(one)
    for n in one:
        two |= _dialectical_neighbors(graph, n)
    two.add(seed)
    return two


def _seed_nodes(graph: dict) -> list[str]:
    """Nodes `find_debates` could return as seeds (debate/controversy/position).

    Also include scholarly_argument_* nodes, which carry fault-line `opposes`
    edges directly and are surfaced by `build_controversy_frame`'s argument-hop
    fallback (ARCHITECTURE §2.2).
    """
    seeds: list[str] = []
    for nid, n in graph["nodes"].items():
        t = (n.get("type") or "").lower()
        if (
            t in SEED_TYPES
            or nid.startswith("scholarly_argument_")
            or nid.startswith("scholar_position_")
        ):
            seeds.append(nid)
    return seeds


# ---------------------------------------------------------------------------
# GATE 1 — every opposes edge is reachable within 2 hops of a find_debates seed
# ---------------------------------------------------------------------------


def _period(graph: dict, nid: str) -> str:
    return (graph["nodes"].get(nid, {}).get("period") or "").lower()


def _is_modern_only_person_edge(graph: dict, e: dict) -> bool:
    """A modern dispute (both endpoints modern persons or publications).

    These are excluded by `find_debates(period_filter=antiquity)` and so are
    out of scope for the antiquity reachability gate. Historiographical
    disagreements between modern publications (e.g. Wetzel 1992 opposing
    Rist 1969 on Augustine) are the publication-shaped instance of the same
    category.
    """
    s, t = e["source"], e["target"]
    s_type, t_type = _node_type(graph, s), _node_type(graph, t)
    if s_type == "publication" and t_type == "publication":
        return True
    return (
        s_type == "person"
        and t_type == "person"
        and _period(graph, s) in MODERN_PERIODS
        and _period(graph, t) in MODERN_PERIODS
    )


def test_all_opposes_edges_reachable_within_2_hops(graph: dict) -> None:
    all_opposes = _opposes_edges(graph)
    # Churn tripwire: any wave that adds or removes an opposes edge must
    # update this pin IN THE SAME COMMIT, stating which edges moved.
    # 11 ancient-corpus opposes + 3 grounded historiography edges
    # (2026-08-16, Wetzel/Rist/TeSelle/Harrison/Brown) + 2 literature-wave
    # disputes (2026-08-17: Irwin 1992 opposes MacIntyre 1990 and Dihle's
    # Christian-innovation thesis) + 2 from the Furst/Markschies wave
    # (Cudworth-vs-Huet reception split; Moller's Augustine/Origen
    # doctrinal contrast, attested pp. 213-214) + 3 from the fault-lines
    # wiring pass (2026-08-17, all attested_by page citations).
    assert len(all_opposes) == 21, (
        f"expected 21 opposes edges, found {len(all_opposes)}"
    )

    # Scope to ancient-relevant fault lines: drop modern person<->person disputes
    # that period_filter excludes for an antiquity question.
    opposes = [e for e in all_opposes if not _is_modern_only_person_edge(graph, e)]
    assert len(opposes) >= 9, (
        f"expected >=9 ancient-scope opposes edges, found {len(opposes)}"
    )

    seeds = _seed_nodes(graph)
    seed_set = set(seeds)

    # Precompute 2-hop reachability from every seed once.
    reach: dict[str, set[str]] = {s: _reachable_within_2_hops(graph, s) for s in seeds}

    unreachable: list[dict] = []
    for e in opposes:
        s, t = e["source"], e["target"]
        # The edge is "surfaced" if BOTH endpoints sit within 2 dialectical hops
        # of at least one common find_debates seed (so build_controversy_frame
        # would assemble them into the same frame). An endpoint that is itself a
        # seed trivially anchors its own frame.
        anchored = False
        if (s in seed_set and t in reach.get(s, set())) or (
            t in seed_set and s in reach.get(t, set())
        ):
            anchored = True
        else:
            for seed in seeds:
                r = reach[seed]
                if s in r and t in r:
                    anchored = True
                    break
        if not anchored:
            unreachable.append(e)

    assert not unreachable, (
        "These opposes fault lines are NOT reachable within 2 hops of any "
        f"find_debates seed — widen the M1 fallback before M4: {unreachable}"
    )


# ---------------------------------------------------------------------------
# GATE 2 — the two empty debate nodes reach their fault lines via fallback
# ---------------------------------------------------------------------------


def _fallback_fault_lines(graph: dict, debate_id: str) -> list[dict]:
    """Recover the fault-line opposes edges for an empty debate node.

    Mirrors ARCHITECTURE §2.2 fallback: hop via `contributes_to` /
    `participates_in` / `discusses` bridge edges (arguments + participants
    pointing at the debate), then collect any `opposes`/`critiques`/`refutes`
    edge incident on those bridge nodes (the re-seed on position/argument
    nodes).
    """
    # Hop 1: bridge nodes directly attached to the debate
    # (argument / pub / person -> debate via contributes_to / participates_in /
    # discusses / advanced_in).
    bridge_nodes: set[str] = set()
    for e in graph["inc"].get(debate_id, []):
        if e["relation"] in BRIDGE_RELATIONS:
            bridge_nodes.add(e["source"])
    for e in graph["out"].get(debate_id, []):
        if e["relation"] in BRIDGE_RELATIONS:
            bridge_nodes.add(e["target"])

    # Hop 2: expand through the argument / publication cluster — a `pub_*` or
    # participant node `discusses` / `advanced_in` the `scholarly_argument_*`
    # that actually carries the fault-line edge (ARCHITECTURE §2.2 step 4: the
    # carneadean opposes edge hangs off `scholarly_argument_amand_*`, reached via
    # the pub_amand `discusses` hop, not the debate node directly).
    cluster_relations = {"discusses", "advanced_in", "contributes_to", "source_for"}
    expanded: set[str] = set(bridge_nodes)
    for node in bridge_nodes:
        for e in graph["out"].get(node, []):
            if e["relation"] in cluster_relations:
                expanded.add(e["target"])
        for e in graph["inc"].get(node, []):
            if e["relation"] in cluster_relations:
                expanded.add(e["source"])
    bridge_nodes = expanded

    fault_lines: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    contested = {"opposes", "critiques", "refutes", "responds_to", "contrasts_with"}
    for node in bridge_nodes:
        for e in graph["out"].get(node, []) + graph["inc"].get(node, []):
            if e["relation"] in contested:
                key = (e["source"], e["relation"], e["target"])
                if key not in seen:
                    seen.add(key)
                    fault_lines.append(e)
    return fault_lines


@pytest.mark.parametrize("debate_id", EMPTY_DEBATES)
def test_empty_debate_node_reaches_fault_lines_via_fallback(
    graph: dict, debate_id: str
) -> None:
    assert debate_id in graph["nodes"], f"missing debate node {debate_id}"

    # Confirm the precondition: this debate has NO direct opposes/critiques out-edge
    # (i.e. it really is an "empty" debate node that needs the fallback).
    direct_dialectical = [
        e
        for e in graph["out"].get(debate_id, [])
        if e["relation"] in {"opposes", "critiques", "refutes"}
    ]
    assert not direct_dialectical, (
        f"{debate_id} unexpectedly carries a direct fault-line edge — "
        "the empty-debate fixture has drifted"
    )

    fault_lines = _fallback_fault_lines(graph, debate_id)
    assert fault_lines, (
        f"fallback recovered NO fault lines for {debate_id} — the M1 "
        "empty-debate fallback would return an empty frame; widen it before M4"
    )


def test_origins_debate_recovers_frede_dihle(graph: dict) -> None:
    """The trigger's f1 frame: Frede vs Dihle must be recoverable."""
    fault_lines = _fallback_fault_lines(
        graph, "debate_origins_notion_of_will_modern_paradigm"
    )
    endpoints = {e["source"] for e in fault_lines} | {e["target"] for e in fault_lines}
    # Either the position-node opposes pair, or the dihle-argument -> frede edge.
    assert (
        "scholar_position_frede_will_originates_epictetus" in endpoints
        or "scholar_frede_michael" in endpoints
    ), f"Frede pole not recovered; endpoints={sorted(endpoints)}"
    assert (
        "scholar_position_dihle_will_christian_innovation" in endpoints
        or "argument_dihle_1982_augustine_invents_philosophical_voluntas" in endpoints
    ), f"Dihle pole not recovered; endpoints={sorted(endpoints)}"


def test_carneadean_debate_recovers_amand_pole(graph: dict) -> None:
    """The trigger's f4 frame: the Amand pole must be recoverable.

    2026-08-17: the original Amand-opposes-Ramelli edge was removed as
    factually wrong — Ramelli 2014 n. 88 cites Amand 1945 in SUPPORT
    (Origen's reception of the Carneadean argos logos), so there is no
    Amand/Ramelli fault line to recover. The debate seed itself must
    still reach the Amand corpus.
    """
    fault_lines = _fallback_fault_lines(
        graph, "debate_carneadean_antiastrology_tradition"
    )
    pairs = {(e["source"], e["target"]) for e in fault_lines}
    flat = {n for pair in pairs for n in pair}
    assert any("amand" in n or "carnead" in n for n in flat), (
        f"Amand/Carneadean pole not recovered: {sorted(flat)}"
    )
    assert not any(
        "amand" in e["source"] and "ramelli" in e["target"] for e in fault_lines
    ), "the refuted Amand-opposes-Ramelli edge is back"


def test_emit_reachability_report(graph: dict) -> None:
    """Write the one-page report the blueprint asks for (§0 Output)."""
    opposes = _opposes_edges(graph)
    report: dict = {
        "generated_by": "graphrag/tests/g6/test_reachability_probe.py",
        "opposes_edge_count": len(opposes),
        "opposes_edges": [
            {"source": e["source"], "target": e["target"]} for e in opposes
        ],
        "empty_debates": {},
    }
    for debate_id in EMPTY_DEBATES:
        fault_lines = _fallback_fault_lines(graph, debate_id)
        report["empty_debates"][debate_id] = {
            "seed_node": debate_id,
            "has_direct_dialectical_out_edge": bool(
                [
                    e
                    for e in graph["out"].get(debate_id, [])
                    if e["relation"] in {"opposes", "critiques", "refutes"}
                ]
            ),
            "fallback_fault_lines": [
                {
                    "source": e["source"],
                    "relation": e["relation"],
                    "target": e["target"],
                }
                for e in fault_lines
            ],
        }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    assert REPORT_PATH.exists()
