#!/usr/bin/env python3
"""Quantify Carnéade → patristique transmission via the EleutherIA KG.

Piste 1 (Paper B target): mechanically reproduce Amand 1945's six-witness
attribution of the Carneadean moral argumentation (« 6 témoins → reconstruction
de l'argumentation morale carnéadienne », Amand p. 571), then push past Amand
by discovering non-tagged arguments that also satisfy the 3/6 attestation rule.

The script is read-only over ``data/kg/nodes.jsonl`` + ``data/kg/edges.jsonl``.
It runs the restricted OWL-RL closure (`materialize_inverses_and_transitivity`),
walks the inferred graph for transmission chains, reconstructs proof chains for
the six Amand pivots, and emits a markdown report (and optionally JSON) suitable
for inclusion in Paper B.

Usage:
    python scripts/analyze_carneadean_transmission.py \
        --output docs/reports/2026-05-16-piste1-carneadean-transmission-analysis.md \
        --depth 5 --format md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict, deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "knowledge graph" / "src"))

from eleutheria_kg.semantic import (  # noqa: E402
    build_graph,
    build_proof_chain,
    materialize_inverses_and_transitivity,
    mint_node_iri,
    serialize_proof_chain,
)
from eleutheria_kg.semantic.vocab import KG, _camel_case  # noqa: E402
from rdflib import Graph, URIRef  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain constants: the six canonical witnesses + the six Amand pivots.
# Witnesses are addressed via their *envelope* (or general-theme) argument node,
# which is the head of the contains-tree built in waves B3-B7.
# ---------------------------------------------------------------------------

WITNESSES: tuple[tuple[str, str, str, str], ...] = (
    (
        "n1",
        "Philo, De Providentia I.79-83",
        "argument_philo_de_providentia_argument_envelope_amand1945",
        "B3",
    ),
    (
        "n2",
        "Alexander of Aphrodisias, De Fato 16-20",
        "argument_alexander_witness2_envelope_amand1945",
        "B4",
    ),
    (
        "n3",
        "Firmicus Maternus, Mathesis I.2.5-11",
        "argument_firmicus_witness3_envelope_amand1945",
        "B4",
    ),
    (
        "n4",
        "Eusebius, Praeparatio Evangelica VI.6.4-21",
        "argument_eus_carneadean_pe_vi_6_general_theme",
        "B6",
    ),
    (
        "n5",
        "John Chrysostom, Hom. post haec Gothi presbyteri sermonem ch. 6",
        "argument_chrysostom_hom_goth_witness5_amand1945",
        "B7",
    ),
    (
        "n6",
        "Ps-Chrysostom, De Fato V",
        "argument_pseudo_chrysostom_de_fato_v_witness6_amand1945",
        "B7",
    ),
)

PIVOTS: tuple[tuple[str, str], ...] = (
    ("argument_carneadean_general_theme_amand1945", "I. Thème général"),
    ("argument_carneadean_legislation_amand1945", "II. Législation"),
    ("argument_carneadean_virtue_vice_amand1945", "III. Vertu & vice"),
    ("argument_carneadean_incentives_amand1945", "IV. Stimulants de l'action"),
    ("argument_carneadean_action_futility_amand1945", "V. Inaction (futilité)"),
    ("argument_carneadean_piety_amand1945", "VI. Piété & religion"),
    (
        "argument_carneadean_stoic_pragmatic_self_refutation_amand1945",
        "VII. Auto-réfutation pragmatique stoïcienne",
    ),
)

PERSON_CARNEADES: str = "person_carneades_214_129bce_l2m3n4o5"

# Persons targeted by the transmission-chain query (witness author → Carneades).
WITNESS_AUTHORS: tuple[tuple[str, str], ...] = (
    ("n1", "person_philo_alexandria_a1b2c3d4"),
    ("n2", "person_alexander_aphrodisias_fl200ce_n5o6p7q8"),
    ("n3", "person_firmicus_maternus_2q7r9t65"),
    ("n4", "person_eusebius_caesarea_d339"),
    ("n5", "person_john_chrysostom_d407"),
    ("n6", "person_pseudo_chrysostom_de_fato"),
)

# Relations that count as attestation of a pivot when emitted by a sub-argument
# or by the witness envelope itself.
ATTEST_RELATIONS: tuple[str, str, str, str] = (
    "evidence_for",
    "extends",
    "employs",
    "discusses",
)

# Edge used to walk from envelope down into sub-arguments (transitive).
CONTAINS_REL = "contains"


# ---------------------------------------------------------------------------
# IRI helpers
# ---------------------------------------------------------------------------


def _rel_iri(relation: str) -> URIRef:
    return URIRef(f"{KG}{_camel_case(relation)}")


def _node_iri(node_id: str) -> URIRef:
    return mint_node_iri(node_id)


def _is_resource(node: URIRef) -> bool:
    return str(node).startswith("https://free-will.app/kg/")


def _resource_id(iri: URIRef) -> str:
    return str(iri).removeprefix("https://free-will.app/kg/")


# ---------------------------------------------------------------------------
# Phase 1: load + materialize
# ---------------------------------------------------------------------------


@dataclass
class GraphState:
    graph: Graph
    pre_graph: Graph
    triples_pre: int
    triples_post: int

    @property
    def inferred(self) -> int:
        return self.triples_post - self.triples_pre


def load_and_materialize(nodes_path: Path, edges_path: Path) -> GraphState:
    """Build the rdflib graph + keep a pristine pre-closure copy for proof reconstruction."""
    pre_graph = build_graph(nodes_path, edges_path)
    pre = len(pre_graph)
    g = Graph()
    for triple in pre_graph:
        g.add(triple)
    materialize_inverses_and_transitivity(g)
    post = len(g)
    logger.info(
        "graph state: %d pre-closure triples, %d post, %d inferred",
        pre,
        post,
        post - pre,
    )
    return GraphState(graph=g, pre_graph=pre_graph, triples_pre=pre, triples_post=post)


# ---------------------------------------------------------------------------
# Phase 2: witness inventory + attestation matrix
# ---------------------------------------------------------------------------


@dataclass
class WitnessInventory:
    label: str
    rank: str
    envelope_id: str
    wave: str
    envelope_exists: bool
    evidenced_passages: list[str] = field(default_factory=list)
    contains_children: list[str] = field(default_factory=list)
    anchoring: str = "absent"  # "passage_anchored" | "envelope_only" | "absent"


def _outgoing_targets(g: Graph, source_iri: URIRef, relation: str) -> list[URIRef]:
    return [
        obj
        for _, _, obj in g.triples((source_iri, _rel_iri(relation), None))
        if isinstance(obj, URIRef)
    ]


def _transitive_successors_via(
    g: Graph, start: URIRef, relation: str
) -> set[URIRef]:
    """BFS over the asserted (or inferred-transitive) ``relation`` property."""
    prop = _rel_iri(relation)
    seen: set[URIRef] = set()
    queue: deque[URIRef] = deque([start])
    while queue:
        cur = queue.popleft()
        for _, _, nxt in g.triples((cur, prop, None)):
            if not isinstance(nxt, URIRef) or nxt in seen:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return seen


def inventory_witnesses(g: Graph) -> list[WitnessInventory]:
    out: list[WitnessInventory] = []
    for rank, label, envelope_id, wave in WITNESSES:
        envelope_iri = _node_iri(envelope_id)
        exists = (envelope_iri, None, None) in g or (
            None,
            None,
            envelope_iri,
        ) in g
        evidenced = [
            _resource_id(t)
            for t in _outgoing_targets(g, envelope_iri, "evidenced_by")
            if _is_resource(t) and _resource_id(t).startswith("passage_")
        ]
        children = sorted(
            _resource_id(t)
            for t in _transitive_successors_via(g, envelope_iri, CONTAINS_REL)
            if _is_resource(t)
        )
        if evidenced:
            anchoring = "passage_anchored"
        elif (
            _outgoing_targets(g, envelope_iri, "cites_primary_source")
            or _outgoing_targets(g, envelope_iri, "discusses")
        ):
            anchoring = "work_anchored"
        else:
            anchoring = "absent"
        out.append(
            WitnessInventory(
                label=label,
                rank=rank,
                envelope_id=envelope_id,
                wave=wave,
                envelope_exists=exists,
                evidenced_passages=evidenced,
                contains_children=children,
                anchoring=anchoring,
            )
        )
    return out


def attestation_matrix(
    g: Graph, witnesses: list[WitnessInventory]
) -> tuple[dict[tuple[str, str], list[str]], dict[str, set[str]]]:
    """Return ((witness_rank, pivot_id) → relations) + (pivot_id → attesting ranks)."""
    matrix: dict[tuple[str, str], list[str]] = {}
    attesters: dict[str, set[str]] = defaultdict(set)
    attest_props = {_rel_iri(rel): rel for rel in ATTEST_RELATIONS}
    for w in witnesses:
        envelope_iri = _node_iri(w.envelope_id)
        candidates: set[URIRef] = {envelope_iri}
        candidates.update(_transitive_successors_via(g, envelope_iri, CONTAINS_REL))
        for pivot_id, _label in PIVOTS:
            pivot_iri = _node_iri(pivot_id)
            relations: list[str] = []
            for cand in candidates:
                for prop_iri, rel_name in attest_props.items():
                    if (cand, prop_iri, pivot_iri) in g:
                        relations.append(rel_name)
                        break
            matrix[(w.rank, pivot_id)] = sorted(set(relations))
            if relations:
                attesters[pivot_id].add(w.rank)
    return matrix, attesters


# ---------------------------------------------------------------------------
# Phase 3: transmission chains person-to-Carneades
# ---------------------------------------------------------------------------


@dataclass
class TransmissionChain:
    rank: str
    author_id: str
    found: bool
    path: list[str] = field(default_factory=list)
    hops: int = 0
    confidences: list[float] = field(default_factory=list)


def _backtrack_path(
    parent: dict[URIRef, URIRef], end: URIRef
) -> list[URIRef]:
    chain: list[URIRef] = [end]
    while chain[-1] in parent:
        chain.append(parent[chain[-1]])
    chain.reverse()
    return chain


def shortest_chain_to_carneades(
    g: Graph, author_iri: URIRef, max_depth: int
) -> list[URIRef] | None:
    """BFS author → Carneades using inverse of ``influences`` (+ ``influenced_by``).

    Carneades has direct ``influences`` edges to several witness authors, so the
    inverse direction is the natural way to climb from author → Carneades.
    """
    carneades_iri = _node_iri(PERSON_CARNEADES)
    if author_iri == carneades_iri:
        return [author_iri]
    inv_props = (_rel_iri("influenced_by"), _rel_iri("follows"))
    # Forward props in case the inverse wasn't materialized for some edges.
    direct_back: tuple[URIRef, ...] = (
        _rel_iri("influences"),
        _rel_iri("precedes"),
    )
    parent: dict[URIRef, URIRef] = {}
    queue: deque[tuple[URIRef, int]] = deque([(author_iri, 0)])
    seen: set[URIRef] = {author_iri}
    while queue:
        cur, depth = queue.popleft()
        if depth >= max_depth:
            continue
        # Forward via inverse properties: cur influenced_by X ⇒ X influences cur
        for prop in inv_props:
            for _, _, nxt in g.triples((cur, prop, None)):
                if not isinstance(nxt, URIRef) or nxt in seen:
                    continue
                seen.add(nxt)
                parent[nxt] = cur
                if nxt == carneades_iri:
                    return _backtrack_path(parent, nxt)
                queue.append((nxt, depth + 1))
        # Fallback via reverse-direction edges asserted with forward props.
        for prop in direct_back:
            for src, _, _ in g.triples((None, prop, cur)):
                if not isinstance(src, URIRef) or src in seen:
                    continue
                seen.add(src)
                parent[src] = cur
                if src == carneades_iri:
                    return _backtrack_path(parent, src)
                queue.append((src, depth + 1))
    return None


def transmission_chains(g: Graph, max_depth: int) -> list[TransmissionChain]:
    out: list[TransmissionChain] = []
    for rank, author_id in WITNESS_AUTHORS:
        author_iri = _node_iri(author_id)
        path = shortest_chain_to_carneades(g, author_iri, max_depth)
        if path is None:
            out.append(
                TransmissionChain(rank=rank, author_id=author_id, found=False)
            )
            continue
        ids = [_resource_id(p) for p in path]
        # Reverse so Carneades comes first (chronological).
        ids.reverse()
        out.append(
            TransmissionChain(
                rank=rank,
                author_id=author_id,
                found=True,
                path=ids,
                hops=len(ids) - 1,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Phase 4: proof chains for each pivot
# ---------------------------------------------------------------------------


@dataclass
class PivotProof:
    pivot_id: str
    label: str
    n_inbound_attestations: int
    sample_chains: list[list[dict[str, Any]]] = field(default_factory=list)
    rule_counts: dict[str, int] = field(default_factory=dict)


def _inbound_attesters(g: Graph, pivot_iri: URIRef) -> list[tuple[URIRef, str]]:
    found: list[tuple[URIRef, str]] = []
    for rel in ATTEST_RELATIONS:
        prop = _rel_iri(rel)
        for src, _, _ in g.triples((None, prop, pivot_iri)):
            if isinstance(src, URIRef):
                found.append((src, rel))
    return found


def proof_chains_for_pivots(
    g: Graph, pre_graph: Graph
) -> list[PivotProof]:
    out: list[PivotProof] = []
    # Only relations whose inverse is registered in CLEAN_INVERSE_PAIRS produce
    # proof chains. ``evidence_for`` is intentionally absent from the ontology's
    # inverse-pairs and won't yield a derivation.
    inv_map = {
        "extends": "extended_by",
        "employs": "employed_by",
        "discusses": "discussed_in",
    }
    for pivot_id, label in PIVOTS:
        pivot_iri = _node_iri(pivot_id)
        inbound = _inbound_attesters(g, pivot_iri)
        rule_counts: dict[str, int] = defaultdict(int)
        samples: list[list[dict[str, Any]]] = []
        seen_samples = 0
        for src_iri, rel in inbound:
            inv_rel = inv_map.get(rel)
            if inv_rel is None:
                continue
            # Reconstruct against the pre-closure graph: build_proof_chain
            # returns [] for triples already in the graph, so we must reason
            # over the un-materialized snapshot.
            claim = (pivot_iri, _rel_iri(inv_rel), src_iri)
            steps = build_proof_chain(pre_graph, claim)
            if not steps:
                continue
            for s in steps:
                rule_counts[s.rule] += 1
            if seen_samples < 3:
                samples.append(serialize_proof_chain(steps))
                seen_samples += 1
        out.append(
            PivotProof(
                pivot_id=pivot_id,
                label=label,
                n_inbound_attestations=len(inbound),
                sample_chains=samples,
                rule_counts=dict(rule_counts),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Phase 5: Carneadean-attested discovery (non-Amand candidates passing 3/6)
# ---------------------------------------------------------------------------


@dataclass
class DiscoveryCandidate:
    arg_id: str
    label: str
    score: int
    witnessing_ranks: list[str]
    relation_summary: dict[str, list[str]]


def iter_argument_ids(nodes_path: Path) -> Iterator[tuple[str, str]]:
    with nodes_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                node = json.loads(line)
            except json.JSONDecodeError:
                continue
            if node.get("type") != "argument":
                continue
            node_id = node.get("id") or ""
            if not node_id:
                continue
            yield node_id, node.get("label") or node_id


def discover_carneadean_candidates(
    g: Graph,
    nodes_path: Path,
    witnesses: list[WitnessInventory],
    *,
    min_score: int = 3,
    skip_amand_tagged: bool = True,
    max_results: int = 20,
) -> list[DiscoveryCandidate]:
    """For each non-Amand argument, count distinct attesting canonical witnesses."""
    witness_pools: dict[str, set[URIRef]] = {}
    for w in witnesses:
        envelope_iri = _node_iri(w.envelope_id)
        pool = {envelope_iri}
        pool.update(_transitive_successors_via(g, envelope_iri, CONTAINS_REL))
        witness_pools[w.rank] = pool
    attest_props = {_rel_iri(rel): rel for rel in ATTEST_RELATIONS}

    candidates: list[DiscoveryCandidate] = []
    for arg_id, label in iter_argument_ids(nodes_path):
        if skip_amand_tagged and arg_id.endswith("_amand1945"):
            continue
        arg_iri = _node_iri(arg_id)
        rel_summary: dict[str, list[str]] = defaultdict(list)
        for w in witnesses:
            pool = witness_pools[w.rank]
            matched: set[str] = set()
            for prop_iri, rel_name in attest_props.items():
                for src, _, _ in g.triples((None, prop_iri, arg_iri)):
                    if isinstance(src, URIRef) and src in pool:
                        matched.add(rel_name)
                        break
            if matched:
                rel_summary[w.rank] = sorted(matched)
        score = len(rel_summary)
        if score >= min_score:
            candidates.append(
                DiscoveryCandidate(
                    arg_id=arg_id,
                    label=label,
                    score=score,
                    witnessing_ranks=sorted(rel_summary.keys()),
                    relation_summary=dict(rel_summary),
                )
            )
    candidates.sort(key=lambda c: (-c.score, c.arg_id))
    return candidates[:max_results]


# ---------------------------------------------------------------------------
# Phase 6: anchoring quality report (derived from Phase 2 inventory)
# ---------------------------------------------------------------------------


def anchoring_summary(witnesses: list[WitnessInventory]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for w in witnesses:
        counts[w.anchoring] += 1
    return dict(counts)


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def _format_witness_matrix(
    witnesses: list[WitnessInventory],
    matrix: dict[tuple[str, str], list[str]],
    attesters: dict[str, set[str]],
) -> str:
    header_cells = [w.rank for w in witnesses]
    lines = [
        "| Pivot \\ Témoin | " + " | ".join(header_cells) + " | Score |",
        "|" + "---|" * (len(header_cells) + 2),
    ]
    for pivot_id, label in PIVOTS:
        row = [label]
        for w in witnesses:
            cell = ", ".join(matrix.get((w.rank, pivot_id), [])) or "—"
            row.append(cell)
        row.append(f"**{len(attesters.get(pivot_id, set()))}/6**")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _format_transmission(chains: list[TransmissionChain]) -> str:
    lines = ["| Rank | Auteur | Trouvé | Hops | Chemin |", "|---|---|---|---|---|"]
    for c in chains:
        path_str = " → ".join(c.path) if c.found else "_no path_"
        lines.append(
            f"| {c.rank} | {c.author_id} | "
            f"{'oui' if c.found else 'non'} | {c.hops if c.found else '—'} | {path_str} |"
        )
    return "\n".join(lines)


def _format_proof_chains(pivots: list[PivotProof]) -> str:
    lines = [
        "| Pivot | Inbound attestations | Règles inférées | Exemples |",
        "|---|---|---|---|",
    ]
    for p in pivots:
        rules = (
            ", ".join(f"{k}={v}" for k, v in sorted(p.rule_counts.items()))
            or "(aucune dérivation supportée par inversion)"
        )
        sample = (
            f"{len(p.sample_chains)} échantillon(s)"
            if p.sample_chains
            else "—"
        )
        lines.append(
            f"| {p.label} | {p.n_inbound_attestations} | {rules} | {sample} |"
        )
    return "\n".join(lines)


def _format_discovery(candidates: list[DiscoveryCandidate]) -> str:
    if not candidates:
        return "_Aucun candidat non-Amand ne satisfait la règle 3/6._"
    lines = [
        "| Argument | Score | Témoins attestants | Relations |",
        "|---|---|---|---|",
    ]
    for c in candidates:
        rels = "; ".join(
            f"{rank}=[{','.join(r)}]" for rank, r in c.relation_summary.items()
        )
        lines.append(
            f"| `{c.arg_id}` — {c.label[:80]} | {c.score}/6 | "
            f"{', '.join(c.witnessing_ranks)} | {rels} |"
        )
    return "\n".join(lines)


def _format_anchoring(witnesses: list[WitnessInventory]) -> str:
    lines = [
        "| Témoin | Envelope ID | Wave | Passages | Sub-args | Anchoring |",
        "|---|---|---|---|---|---|",
    ]
    for w in witnesses:
        lines.append(
            f"| {w.rank} — {w.label} | `{w.envelope_id}` | {w.wave} | "
            f"{len(w.evidenced_passages)} | {len(w.contains_children)} | "
            f"**{w.anchoring}** |"
        )
    return "\n".join(lines)


def render_markdown(
    *,
    state: GraphState,
    witnesses: list[WitnessInventory],
    matrix: dict[tuple[str, str], list[str]],
    attesters: dict[str, set[str]],
    chains: list[TransmissionChain],
    pivots: list[PivotProof],
    candidates: list[DiscoveryCandidate],
    timestamp: str,
) -> str:
    template_path = (
        ROOT / "docs" / "reports" / "2026-05-16-piste1-transmission-analysis-TEMPLATE.md"
    )
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _DEFAULT_TEMPLATE
    anchoring = anchoring_summary(witnesses)
    witnesses_passage = anchoring.get("passage_anchored", 0)
    witnesses_envelope = anchoring.get("work_anchored", 0)
    witnesses_absent = anchoring.get("absent", 0)
    pivots_passing = sum(1 for p in PIVOTS if len(attesters.get(p[0], set())) >= 3)
    return (
        template.replace("{{TIMESTAMP}}", timestamp)
        .replace("{{TRIPLES_PRE}}", str(state.triples_pre))
        .replace("{{TRIPLES_POST}}", str(state.triples_post))
        .replace("{{INFERRED_TRIPLES}}", str(state.inferred))
        .replace("{{ANCHORING_TABLE}}", _format_anchoring(witnesses))
        .replace("{{WITNESSES_PASSAGE_ANCHORED}}", str(witnesses_passage))
        .replace("{{WITNESSES_WORK_ANCHORED}}", str(witnesses_envelope))
        .replace("{{WITNESSES_ABSENT}}", str(witnesses_absent))
        .replace(
            "{{WITNESS_MATRIX}}",
            _format_witness_matrix(witnesses, matrix, attesters),
        )
        .replace("{{PIVOTS_PASSING_3_OF_6}}", str(pivots_passing))
        .replace("{{TRANSMISSION_TABLE}}", _format_transmission(chains))
        .replace("{{PROOF_CHAIN_TABLE}}", _format_proof_chains(pivots))
        .replace("{{DISCOVERY_TABLE}}", _format_discovery(candidates))
        .replace("{{N_DISCOVERY_CANDIDATES}}", str(len(candidates)))
    )


_DEFAULT_TEMPLATE = """---
title: Piste 1 — Quantification mécanique de la transmission carnéadienne
date: {{TIMESTAMP}}
kg_triples_pre: {{TRIPLES_PRE}}
kg_triples_post: {{TRIPLES_POST}}
inferred_triples: {{INFERRED_TRIPLES}}
---

# Piste 1 — Transmission Carnéade → patristique : analyse mécanique

## Phase 1 — Closure OWL-RL

- Triples avant closure : **{{TRIPLES_PRE}}**
- Triples après closure : **{{TRIPLES_POST}}**
- Triples inférés : **{{INFERRED_TRIPLES}}**

## Phase 2 — Inventaire des 6 témoins canoniques

{{ANCHORING_TABLE}}

## Phase 3 — Matrice d'attestation 6×6

Règle Amand p. 571 : un pivot est carnéadien s'il est attesté par ≥ 3 des 6 témoins.

{{WITNESS_MATRIX}}

Pivots satisfaisant la règle 3/6 : **{{PIVOTS_PASSING_3_OF_6}}/{{N_PIVOTS}}**

## Phase 4 — Chaînes de transmission auteur → Carnéade

{{TRANSMISSION_TABLE}}

## Phase 5 — Proof chains pour les pivots Amand

{{PROOF_CHAIN_TABLE}}

## Phase 6 — Découverte mécanique post-Amand

Candidats non taggés `amand1945` satisfaisant la règle 3/6 d'attestation par les 6 témoins canoniques :

{{DISCOVERY_TABLE}}

Total candidats : **{{N_DISCOVERY_CANDIDATES}}**

## Phase 7 — Diagnostic d'ancrage

- Témoins passage-anchored : **{{WITNESSES_PASSAGE_ANCHORED}}/6**
- Témoins work-anchored seulement : **{{WITNESSES_WORK_ANCHORED}}/6**
- Témoins totalement non-anchored : **{{WITNESSES_ABSENT}}/6**

## Conclusion

(à compléter manuellement après lecture du tableau ci-dessus)
"""


def render_json(
    *,
    state: GraphState,
    witnesses: list[WitnessInventory],
    matrix: dict[tuple[str, str], list[str]],
    attesters: dict[str, set[str]],
    chains: list[TransmissionChain],
    pivots: list[PivotProof],
    candidates: list[DiscoveryCandidate],
    timestamp: str,
) -> str:
    payload: dict[str, Any] = {
        "timestamp": timestamp,
        "graph": {
            "triples_pre": state.triples_pre,
            "triples_post": state.triples_post,
            "inferred": state.inferred,
        },
        "witnesses": [
            {
                "rank": w.rank,
                "label": w.label,
                "envelope_id": w.envelope_id,
                "wave": w.wave,
                "envelope_exists": w.envelope_exists,
                "evidenced_passages": w.evidenced_passages,
                "n_contains_children": len(w.contains_children),
                "anchoring": w.anchoring,
            }
            for w in witnesses
        ],
        "attestation_matrix": [
            {
                "witness_rank": rank,
                "pivot_id": pid,
                "relations": matrix.get((rank, pid), []),
            }
            for rank, _, _, _ in WITNESSES
            for pid, _ in PIVOTS
        ],
        "attesters_per_pivot": {
            pid: sorted(attesters.get(pid, set())) for pid, _ in PIVOTS
        },
        "transmission_chains": [
            {
                "rank": c.rank,
                "author_id": c.author_id,
                "found": c.found,
                "hops": c.hops,
                "path": c.path,
            }
            for c in chains
        ],
        "pivot_proof_chains": [
            {
                "pivot_id": p.pivot_id,
                "label": p.label,
                "n_inbound_attestations": p.n_inbound_attestations,
                "rule_counts": p.rule_counts,
                "sample_chains": p.sample_chains,
            }
            for p in pivots
        ],
        "discovery_candidates": [
            {
                "arg_id": c.arg_id,
                "label": c.label,
                "score": c.score,
                "witnessing_ranks": c.witnessing_ranks,
                "relation_summary": c.relation_summary,
            }
            for c in candidates
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--nodes", default="data/kg/nodes.jsonl", type=Path)
    p.add_argument("--edges", default="data/kg/edges.jsonl", type=Path)
    p.add_argument(
        "--output",
        type=Path,
        default=Path("docs/reports/2026-05-16-piste1-carneadean-transmission-analysis.md"),
    )
    p.add_argument("--depth", type=int, default=5, help="BFS depth for transmission chains")
    p.add_argument(
        "--format",
        choices=("md", "json", "both"),
        default="md",
    )
    p.add_argument(
        "--max-discovery",
        type=int,
        default=20,
        help="Cap on the number of post-Amand discovery candidates returned.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    nodes_path = args.nodes if args.nodes.is_absolute() else ROOT / args.nodes
    edges_path = args.edges if args.edges.is_absolute() else ROOT / args.edges
    if not nodes_path.exists() or not edges_path.exists():
        raise SystemExit(f"Missing KG snapshot: {nodes_path}, {edges_path}")

    timestamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
    state = load_and_materialize(nodes_path, edges_path)
    witnesses = inventory_witnesses(state.graph)
    matrix, attesters = attestation_matrix(state.graph, witnesses)
    chains = transmission_chains(state.graph, args.depth)
    pivots = proof_chains_for_pivots(state.graph, state.pre_graph)
    candidates = discover_carneadean_candidates(
        state.graph,
        nodes_path,
        witnesses,
        max_results=args.max_discovery,
    )

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.format in ("md", "both"):
        md = render_markdown(
            state=state,
            witnesses=witnesses,
            matrix=matrix,
            attesters=attesters,
            chains=chains,
            pivots=pivots,
            candidates=candidates,
            timestamp=timestamp,
        ).replace("{{N_PIVOTS}}", str(len(PIVOTS)))
        md_path = output.with_suffix(".md")
        md_path.write_text(md, encoding="utf-8")
        logger.info("wrote %s", md_path)

    if args.format in ("json", "both"):
        js = render_json(
            state=state,
            witnesses=witnesses,
            matrix=matrix,
            attesters=attesters,
            chains=chains,
            pivots=pivots,
            candidates=candidates,
            timestamp=timestamp,
        )
        js_path = output.with_suffix(".json")
        js_path.write_text(js, encoding="utf-8")
        logger.info("wrote %s", js_path)

    print(
        f"[piste1] inferred={state.inferred} "
        f"passage_anchored={anchoring_summary(witnesses).get('passage_anchored', 0)}/6 "
        f"pivots_passing_3_of_6={sum(1 for p in PIVOTS if len(attesters.get(p[0], set())) >= 3)}/{len(PIVOTS)} "
        f"discovery_candidates={len(candidates)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
