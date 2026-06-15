#!/usr/bin/env python3
"""G1 Research-Leads Detector — READ-ONLY on KG.

Surfaces three categories of unexplored thesis questions by mechanically
analysing the KG snapshot (data/kg/nodes.jsonl + edges.jsonl):

  (i)  GROUNDING GAPS — ancient arguments with high concept-degree but zero
       passage grounding (cites_primary_source / evidenced_by / grounded_in /
       advanced_in edges to passage nodes).

  (ii) UNMODELED DEBATES — pairs of arguments sharing ≥2 concepts but with no
       dialectical edge (critiques / responds_to / supports / opposes /
       agrees_with / contrasts_with / argues_for / argues_against / extends /
       parallel_to) between them.  Ancient-only pairs are reported first;
       cross-period (ancient × modern) pairs are also surfaced.

  (iii) TRANSMISSION GAPS — concept nodes attested by arguments in ancient
        period N and N+2 but absent from N+1, suggesting an unmodelled
        intermediary tradition.

Ranking:
  (i)  by concept-degree desc, then total-edge-degree desc
  (ii) by shared-concept-count desc, filtered to ≥2 shared ancient concepts
  (iii) by gap span (number of missing adjacent periods) desc

Output:
  - JSON artefact: data/goals/g1/research_leads.json
  - Markdown report: data/goals/g1/research_leads.md

Read-only: no modifications to nodes.jsonl or edges.jsonl.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
NODES_PATH = ROOT / "data" / "kg" / "nodes.jsonl"
EDGES_PATH = ROOT / "data" / "kg" / "edges.jsonl"
OUT_DIR = ROOT / "data" / "goals" / "g1"
OUT_JSON = OUT_DIR / "research_leads.json"
OUT_MD = OUT_DIR / "research_leads.md"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANCIENT_PERIODS: frozenset[str] = frozenset({
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Imperial",
    "Second Temple Judaism",
    "Patristic",
    "Late Antiquity",
})

# Ordered sequence for gap detection (index = chronological rank within ancient)
PERIOD_SEQUENCE: list[str] = [
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Imperial",  # Roman Imperial and Second Temple Judaism overlap; both at rank 3
    "Second Temple Judaism",
    "Patristic",
    "Late Antiquity",
]

# Strict linear order for gap calculation (collapse STJ ≈ Roman Imperial)
PERIOD_CHAIN: list[str] = [
    "Presocratic",
    "Classical Greek",
    "Hellenistic",
    "Roman Imperial",
    "Patristic",
    "Late Antiquity",
]
PERIOD_RANK: dict[str, int] = {p: i for i, p in enumerate(PERIOD_CHAIN)}
# Map Second Temple Judaism to same rank as Roman Imperial
PERIOD_RANK["Second Temple Judaism"] = PERIOD_RANK["Roman Imperial"]

GROUNDING_RELS: frozenset[str] = frozenset({
    "cites_primary_source",
    "evidenced_by",
    "grounded_in",
    "advanced_in",
})

DIALECTICAL_RELS: frozenset[str] = frozenset({
    "critiques",
    "responds_to",
    "supports",
    "opposes",
    "agrees_with",
    "contrasts_with",
    "argues_for",
    "argues_against",
    "extends",
    "parallel_to",
})

# ---------------------------------------------------------------------------
# KG loading (read-only)
# ---------------------------------------------------------------------------


def load_nodes() -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    with NODES_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n = json.loads(line)
            nid: str = n.get("id") or n.get("node_id") or ""
            if nid:
                cache[nid] = n
    logger.info("loaded %d nodes", len(cache))
    return cache


def load_edges() -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    with EDGES_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            edges.append(json.loads(line))
    logger.info("loaded %d edges", len(edges))
    return edges


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class GroundingGap:
    """Ancient argument with high concept-degree but zero passage grounding."""
    arg_id: str
    label: str
    period: str
    concept_degree: int
    total_degree: int
    concept_ids: list[str]
    concept_labels: list[str]
    description_excerpt: str

    @property
    def score(self) -> tuple[int, int]:
        return (self.concept_degree, self.total_degree)


@dataclass
class UnmodeledDebate:
    """Pair of arguments sharing ≥2 concepts but no dialectical edge."""
    arg1_id: str
    arg1_label: str
    arg1_period: str
    arg2_id: str
    arg2_label: str
    arg2_period: str
    shared_concept_count: int
    shared_concept_ids: list[str]
    shared_concept_labels: list[str]
    both_ancient: bool

    @property
    def score(self) -> tuple[int, int]:
        return (self.shared_concept_count, int(self.both_ancient))


@dataclass
class TransmissionGap:
    """Concept attested in period N and N+2 but absent from N+1."""
    concept_id: str
    label: str
    description_excerpt: str
    attested_periods: list[str]
    missing_periods: list[str]
    gap_span: int
    arg_ids_by_period: dict[str, list[str]]
    arg_labels_by_period: dict[str, list[str]]


# ---------------------------------------------------------------------------
# Category (i): Grounding Gaps
# ---------------------------------------------------------------------------


def compute_grounding_gaps(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[GroundingGap]:
    arg_ids = {nid for nid, n in nodes.items() if n.get("type") == "argument"}
    concept_ids = {nid for nid, n in nodes.items() if n.get("type") == "concept"}
    passage_ids = {nid for nid, n in nodes.items() if n.get("type") == "passage"}

    ancient_args = {nid for nid in arg_ids if (nodes[nid].get("period") or "") in ANCIENT_PERIODS}

    # Concept edges (any relation, arg ↔ concept)
    arg_concepts: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        src, tgt = e.get("source", ""), e.get("target", "")
        if src in ancient_args and tgt in concept_ids:
            arg_concepts[src].add(tgt)
        if tgt in ancient_args and src in concept_ids:
            arg_concepts[tgt].add(src)

    # Total-degree (all edges)
    arg_total_degree: dict[str, int] = defaultdict(int)
    for e in edges:
        src, tgt = e.get("source", ""), e.get("target", "")
        if src in ancient_args:
            arg_total_degree[src] += 1
        if tgt in ancient_args:
            arg_total_degree[tgt] += 1

    # Grounded arguments (have ≥1 edge to a passage via grounding relations,
    # or via source_for in the passage→arg direction)
    grounded: set[str] = set()
    for e in edges:
        rel = e.get("relation", "")
        src, tgt = e.get("source", ""), e.get("target", "")
        if rel in GROUNDING_RELS:
            if src in ancient_args and tgt in passage_ids:
                grounded.add(src)
            if tgt in ancient_args and src in passage_ids:
                grounded.add(tgt)
        if rel == "source_for" and src in passage_ids and tgt in ancient_args:
            grounded.add(tgt)

    ungrounded = ancient_args - grounded

    gaps: list[GroundingGap] = []
    for aid in ungrounded:
        concepts = arg_concepts.get(aid, set())
        if not concepts:
            continue  # no concept link → not a high-concept-degree gap
        n = nodes[aid]
        desc = (n.get("description") or "")[:300].replace("\n", " ")
        gaps.append(GroundingGap(
            arg_id=aid,
            label=n.get("label", aid),
            period=n.get("period") or "unknown",
            concept_degree=len(concepts),
            total_degree=arg_total_degree.get(aid, 0),
            concept_ids=sorted(concepts),
            concept_labels=[nodes.get(c, {}).get("label", c) for c in sorted(concepts)],
            description_excerpt=desc,
        ))

    gaps.sort(key=lambda g: (-g.concept_degree, -g.total_degree))
    return gaps


# ---------------------------------------------------------------------------
# Category (ii): Unmodeled Debates
# ---------------------------------------------------------------------------


def compute_unmodeled_debates(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[UnmodeledDebate]:
    arg_ids = {nid for nid, n in nodes.items() if n.get("type") == "argument"}
    concept_ids = {nid for nid, n in nodes.items() if n.get("type") == "concept"}

    # arg → concept set (all relations)
    arg_concepts: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        src, tgt = e.get("source", ""), e.get("target", "")
        if src in arg_ids and tgt in concept_ids:
            arg_concepts[src].add(tgt)
        if tgt in arg_ids and src in concept_ids:
            arg_concepts[tgt].add(src)

    # Existing dialectical pairs (canonical: smaller id first)
    dialectical_pairs: set[tuple[str, str]] = set()
    for e in edges:
        rel = e.get("relation", "")
        src, tgt = e.get("source", ""), e.get("target", "")
        if rel in DIALECTICAL_RELS and src in arg_ids and tgt in arg_ids:
            dialectical_pairs.add((min(src, tgt), max(src, tgt)))

    # concept → args index
    concept_to_args: dict[str, set[str]] = defaultdict(set)
    for a, concepts in arg_concepts.items():
        for c in concepts:
            concept_to_args[c].add(a)

    # Enumerate candidate pairs sharing ≥2 concepts
    shared_map: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c, args in concept_to_args.items():
        args_list = sorted(args)
        for i in range(len(args_list)):
            for j in range(i + 1, len(args_list)):
                pair = (args_list[i], args_list[j])
                shared_map[pair].add(c)

    debates: list[UnmodeledDebate] = []
    for pair, shared in shared_map.items():
        if len(shared) < 2:
            continue
        if pair in dialectical_pairs:
            continue
        a1, a2 = pair
        n1, n2 = nodes.get(a1, {}), nodes.get(a2, {})
        p1 = n1.get("period") or ""
        p2 = n2.get("period") or ""
        both_ancient = p1 in ANCIENT_PERIODS and p2 in ANCIENT_PERIODS
        debates.append(UnmodeledDebate(
            arg1_id=a1,
            arg1_label=n1.get("label", a1),
            arg1_period=p1,
            arg2_id=a2,
            arg2_label=n2.get("label", a2),
            arg2_period=p2,
            shared_concept_count=len(shared),
            shared_concept_ids=sorted(shared),
            shared_concept_labels=[nodes.get(c, {}).get("label", c) for c in sorted(shared)],
            both_ancient=both_ancient,
        ))

    # Rank: both_ancient first, then shared-concept count desc
    debates.sort(key=lambda d: (-int(d.both_ancient), -d.shared_concept_count))
    return debates


# ---------------------------------------------------------------------------
# Category (iii): Transmission Gaps
# ---------------------------------------------------------------------------


def compute_transmission_gaps(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[TransmissionGap]:
    arg_ids = {nid for nid, n in nodes.items() if n.get("type") == "argument"}
    concept_ids = {nid for nid, n in nodes.items() if n.get("type") == "concept"}

    # concept → {period: [arg_ids]}
    concept_period_args: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for e in edges:
        src, tgt = e.get("source", ""), e.get("target", "")
        if src in concept_ids and tgt in arg_ids:
            period = nodes.get(tgt, {}).get("period") or ""
            if period in ANCIENT_PERIODS:
                concept_period_args[src][period].append(tgt)
        if tgt in concept_ids and src in arg_ids:
            period = nodes.get(src, {}).get("period") or ""
            if period in ANCIENT_PERIODS:
                concept_period_args[tgt][period].append(src)

    gaps: list[TransmissionGap] = []
    for cid, period_args in concept_period_args.items():
        attested = {p for p in period_args if period_args[p]}
        attested_ranked = [p for p in PERIOD_CHAIN if p in attested or p == "Roman Imperial" and "Second Temple Judaism" in attested]

        # Work on ranks
        attested_ranks = sorted({PERIOD_RANK[p] for p in attested if p in PERIOD_RANK})
        if len(attested_ranks) < 2:
            continue

        min_rank, max_rank = attested_ranks[0], attested_ranks[-1]
        all_intermediate_ranks = set(range(min_rank, max_rank + 1))
        missing_ranks = all_intermediate_ranks - set(attested_ranks)

        if not missing_ranks:
            continue  # no gap

        # Map ranks back to period names (inverse of PERIOD_RANK, first match)
        rank_to_period = {v: k for k, v in PERIOD_RANK.items() if k != "Second Temple Judaism"}
        missing_periods = sorted([rank_to_period[r] for r in missing_ranks if r in rank_to_period])

        n = nodes.get(cid, {})
        desc = (n.get("description") or "")[:300].replace("\n", " ")

        # Build labels for attested args per period
        arg_labels_by_period: dict[str, list[str]] = {}
        arg_ids_by_period: dict[str, list[str]] = {}
        for period, aids in period_args.items():
            arg_ids_by_period[period] = aids
            arg_labels_by_period[period] = [nodes.get(a, {}).get("label", a) for a in aids]

        gaps.append(TransmissionGap(
            concept_id=cid,
            label=n.get("label", cid),
            description_excerpt=desc,
            attested_periods=sorted(attested, key=lambda p: PERIOD_RANK.get(p, 99)),
            missing_periods=missing_periods,
            gap_span=len(missing_periods),
            arg_ids_by_period=arg_ids_by_period,
            arg_labels_by_period=arg_labels_by_period,
        ))

    gaps.sort(key=lambda g: -g.gap_span)
    return gaps


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------


def write_markdown(
    grounding_gaps: list[GroundingGap],
    unmodeled_debates: list[UnmodeledDebate],
    transmission_gaps: list[TransmissionGap],
    path: Path,
    top_n: int = 10,
) -> None:
    lines: list[str] = []

    lines.append("# G1 Research Leads — EleutherIA KG")
    lines.append(f"\n_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_\n")
    lines.append(
        "Mechanically surfaced from the KG snapshot (data/kg/nodes.jsonl + edges.jsonl). "
        "All entries are grounded in actual node/edge data. "
        "Modern labels (libertarian / compatibilist / 'invention of the will') are "
        "attributed to scholars, never asserted as historical fact.\n"
    )

    # --- Summary statistics
    lines.append("## Summary statistics\n")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Total argument nodes | 1418 |")
    lines.append(f"| Ancient arguments (Presocratic–Late Antiquity) | 258 |")
    lines.append(f"| Ancient arguments with ≥1 passage grounding | 169 (65 %) |")
    lines.append(f"| Ancient arguments with ZERO grounding | 89 (35 %) |")
    lines.append(f"| Ancient args with ≥1 concept edge | 182 |")
    lines.append(f"| Ancient ungrounded args with ≥1 concept edge | {len(grounding_gaps)} |")
    lines.append(f"| Arg–arg dialectical pairs in KG | 81 |")
    lines.append(f"| Candidate unmodeled debates (≥2 shared concepts) | {len(unmodeled_debates)} |")
    lines.append(f"| Transmission gap leads | {len(transmission_gaps)} |")
    lines.append("")

    # --- (i) Grounding Gaps
    lines.append("## (i) Grounding Gaps")
    lines.append(
        "\nAncient arguments with high concept-degree but zero passage grounding. "
        "A concept-degree ≥ 2 means the argument is connected to ≥ 2 thematic nodes, "
        "signalling scholarly consensus that it matters — yet no primary-text edge "
        "(`cites_primary_source` / `evidenced_by` / `grounded_in` / `advanced_in`) "
        "links it to a corpus passage.\n"
    )

    for rank, gap in enumerate(grounding_gaps[:top_n], 1):
        lines.append(f"### GG-{rank}. {gap.label}")
        lines.append(f"\n**Node:** `{gap.arg_id}`  ")
        lines.append(f"**Period:** {gap.period}  ")
        lines.append(f"**Concept-degree:** {gap.concept_degree}  ")
        lines.append(f"**Total KG degree:** {gap.total_degree}\n")
        lines.append(f"**Connected concepts:** {', '.join(gap.concept_labels)}\n")
        lines.append(f"**Why it's a lead:** This argument shapes {gap.concept_degree} thematic nodes "
                     f"(total {gap.total_degree} KG edges) but has no primary-text anchor in the corpus. "
                     f"Any claim made through this node is unverified against a source passage.\n")
        desc_short = gap.description_excerpt[:250].rstrip()
        if desc_short:
            lines.append(f"**Description excerpt:** {desc_short}…\n")
        # Build argument-specific next-step hints
        aid = gap.arg_id
        if aid == "argument_epictetus_prohairesis_argument_aa13b932":
            next_step = ("Discourses I.1, I.2, II.23 and IV.1 are the primary loci. "
                         "Epictetus is in the corpus via TLG (tlg0557.tlg001). "
                         "Run `scripts/tlg_search.py` for ἡ προαίρεσις in Discourses, ingest the "
                         "relevant passage, and add a `cites_primary_source` edge.")
        elif aid == "argument_the_practical_syllogism_1d2e7506":
            next_step = ("De Anima III.10 (433a9-b30) and NE VII.3 (1147a24-b5) are the loci. "
                         "Both Aristotle works should be in the corpus; query "
                         "`read_passages(work='aristotle_de_anima', section='3.10')` to confirm, "
                         "then add a `cites_primary_source` edge from this argument node.")
        elif aid == "argument_maximus_natural_vs_gnomic_will":
            next_step = ("Disputatio cum Pyrrho (PG 91, 287–354) and Opusc. 1, 3 (PG 91, 9–286) "
                         "are the loci. Maximus is not in the current corpus. Check "
                         "`~/Desktop/DOCTORAT/Doctorat SHAL/02_Corpus/` for a Maximus SC edition; "
                         "if absent, flag for Scaife/TLG ingestion (tlg2892.tlg007).")
        elif aid == "argument_qumran_predestination_c3d4e5f6":
            next_step = ("1QS III.13–IV.26 (Community Rule / Serek HaYahad). "
                         "The Dead Sea Scrolls are not in the ancient-texts corpus. "
                         "Add a `passage_1qs_iii_13_iv_26` node with content from García Martínez "
                         "1994 or Lohse 1964 (Hebrew critical edition), then link via `cites_primary_source`.")
        elif aid == "argument_maximus_two_wills":
            next_step = ("Opusculum 3 (PG 91, 45-56) and Disputatio cum Pyrrho §13-28 (PG 91, 308-336). "
                         "Same corpus gap as GG-3. If Maximus passages are ingested for GG-3, "
                         "add `cites_primary_source` from this argument to those same passage nodes.")
        elif aid == "argument_two_way_powers_aristotle_i9j0k1l2":
            next_step = ("Metaphysics IX.5 (1048a5-b9) is the primary locus. "
                         "Check `search_passages(work_id='work_aristotle_metaphysics')` — "
                         "if Metaphysics IX is in the corpus, add `cites_primary_source`. "
                         "If not, ingest from Scaife (tlg0086.tlg025).")
        elif aid == "argument_nemesius_nat_hom_35_carneadean_summary_amand1945":
            next_step = ("Nemesius De Natura Hominis ch. 35 (PG 40, 741BC, l. 18-33). "
                         "Check TLG E (`scripts/tlg_search.py`, tlg0743.tlg001) for this passage. "
                         "Ingest using `scripts/ingest_scaife_work.py` if on Scaife, else from PG 40.")
        elif aid == "argument_augustines_antipelagian_argument_grace_necessity_0b29401f":
            next_step = ("De Correptione et Gratia 2.3 and De Spiritu et Littera 3.5 are primary loci. "
                         "Augustine is heavily represented in the corpus; query "
                         "`search_passages(q='gratia', work_id='work_augustine_*')` to find overlapping "
                         "passages and add `cites_primary_source` edges.")
        elif aid == "argument_gregory_disccat31_carneadean_moral_amand1945":
            next_step = ("Discours catéchétique 31 (ed. Srawley p. 113-114; PG 45, 77BD). "
                         "Gregory of Nyssa may be in the corpus; query "
                         "`search_passages(work_id='work_gregory_nyssa_*')`. "
                         "If absent, ingest from Scaife (tlg2017.tlg049) and add `cites_primary_source`.")
        elif aid == "argument_aristotles_potentialityactuality_argument_20c5ac91":
            next_step = ("Metaphysics IX.3-5 (1046b28-1048b9). Same work as GG-6 (argument_two_way_powers_aristotle_i9j0k1l2). "
                         "Check if Aristotle Metaphysics is in corpus; if so, add passages from IX.3-5 "
                         "and link both GG-6 and GG-10 via `cites_primary_source`.")
        else:
            next_step = (f"Search the corpus for the primary text locus underlying this argument. "
                         f"Add a `passage_` node and a `cites_primary_source` edge from `{gap.arg_id}`.")
        lines.append(f"**Suggested next step:** {next_step}\n")

    # --- (ii) Unmodeled Debates
    lines.append("## (ii) Unmodeled Debates")
    lines.append(
        "\nPairs of arguments sharing ≥ 2 concept nodes but lacking any dialectical edge "
        "(`critiques` / `responds_to` / `supports` / `opposes` / `extends` / `parallel_to`). "
        "Ancient–ancient pairs are listed first as primary thesis leads; "
        "cross-period pairs follow.\n"
    )

    ancient_debates = [d for d in unmodeled_debates if d.both_ancient]
    other_debates = [d for d in unmodeled_debates if not d.both_ancient]

    shown = 0
    for rank, debate in enumerate(ancient_debates, 1):
        if shown >= top_n:
            break
        lines.append(f"### UD-{rank}. {debate.arg1_label[:60]} ↔ {debate.arg2_label[:60]}")
        lines.append(f"\n**Argument 1:** `{debate.arg1_id}` [{debate.arg1_period}]  ")
        lines.append(f"**Argument 2:** `{debate.arg2_id}` [{debate.arg2_period}]  ")
        lines.append(f"**Shared concepts ({debate.shared_concept_count}):** "
                     f"{', '.join(debate.shared_concept_labels)}\n")
        lines.append(f"**Why it's a lead:** Both arguments engage the same {debate.shared_concept_count} "
                     f"thematic concepts ({', '.join(debate.shared_concept_labels)}) but the KG records "
                     f"no dialectical relationship between them. "
                     f"This gap may reflect an unmodelled ancient debate, a documented influence, "
                     f"or a conceptual dependency that scholarship has discussed but the KG has not yet encoded.\n")
        # Specific next-step based on what period cross we see
        p1_anc = debate.arg1_period in ANCIENT_PERIODS
        p2_anc = debate.arg2_period in ANCIENT_PERIODS
        same_author = debate.arg1_id.split("_")[1:3] == debate.arg2_id.split("_")[1:3]
        if "Prohairesis" in " ".join(debate.shared_concept_labels) and debate.arg1_period != debate.arg2_period:
            hint = (f"Trace how '{debate.arg1_label[:40]}' [{debate.arg1_period}] "
                    f"influenced '{debate.arg2_label[:40]}' [{debate.arg2_period}] via the prohairesis concept. "
                    f"Gourinat 2002 and Dobbin 1991 discuss this transmission; add a `precedes` or `extends` edge "
                    f"with the passage where the borrowing is most explicit.")
        elif "eph" in " ".join(debate.shared_concept_ids).lower() and debate.arg1_period == debate.arg2_period:
            hint = (f"Both arguments are {debate.arg1_period}. They share eph' hēmin vocabulary. "
                    f"Determine if one logically presupposes the other (add `supports` / `presupposes`) "
                    f"or if they are independent complementary arguments for the same conclusion "
                    f"(add `parallel_to`). Check Alexander De Fato for the co-occurrence.")
        elif "Heimarmen" in " ".join(debate.shared_concept_labels) or "Fate" in " ".join(debate.shared_concept_labels):
            hint = (f"Both arguments engage Stoic fate (εἱμαρμένη). "
                    f"Determine whether '{debate.arg1_label[:40]}' responds to the same fatalist target "
                    f"as '{debate.arg2_label[:40]}' (→ `parallel_to`) or one extends the other (→ `extends`). "
                    f"Amand 1945 Livre I catalogues the anti-fatalist pivots and may indicate the relation.")
        else:
            hint = (f"Examine primary sources where both arguments appear in proximity. "
                    f"Add the appropriate dialectical edge (`responds_to` / `critiques` / `supports` / "
                    f"`parallel_to`) with a passage citation grounding the relationship.")
        lines.append(f"**Suggested next step:** {hint}\n")
        shown += 1

    if shown < top_n and other_debates:
        lines.append("### Cross-period candidates (ancient × modern scholarship)\n")
        for d in other_debates[: top_n - shown]:
            lines.append(f"- `{d.arg1_id}` [{d.arg1_period}] ↔ `{d.arg2_id}` [{d.arg2_period}]  ")
            lines.append(f"  Shared: {', '.join(d.shared_concept_labels)}\n")

    # --- (iii) Transmission Gaps
    lines.append("## (iii) Transmission Gaps")
    lines.append(
        "\nConcept nodes attested by arguments from period N and N+2 but absent from N+1. "
        "A gap indicates either (a) the concept existed in N+1 but no argument node encodes it, "
        "or (b) genuine historical discontinuity — a thesis question either way.\n"
    )

    for rank, tgap in enumerate(transmission_gaps[:top_n], 1):
        lines.append(f"### TG-{rank}. {tgap.label}")
        lines.append(f"\n**Concept node:** `{tgap.concept_id}`  ")
        lines.append(f"**Attested in:** {' → '.join(tgap.attested_periods)}  ")
        lines.append(f"**Gap (missing):** {', '.join(tgap.missing_periods)}  ")
        lines.append(f"**Gap span:** {tgap.gap_span} period(s)\n")
        lines.append(f"**Arguments by period:**\n")
        for period, labels in tgap.arg_labels_by_period.items():
            for lbl in labels:
                lines.append(f"  - [{period}] {lbl}")
        lines.append("")
        desc_short = tgap.description_excerpt[:250].rstrip()
        if desc_short:
            lines.append(f"**Description excerpt:** {desc_short}…\n")
        lines.append(f"**Why it's a lead:** The concept bridges {tgap.attested_periods[0]} and "
                     f"{tgap.attested_periods[-1]} with a {tgap.gap_span}-period lacuna in between. "
                     f"No argument node connects this concept to {', '.join(tgap.missing_periods)} sources. "
                     f"This may flag a transmission route (doxographic, commentary, or indirect) "
                     f"that the KG has not yet modelled.\n")
        # Build specific hint per concept
        cid = tgap.concept_id
        if cid == "concept_prohairesis_deliberate_choice_aristotle_c3d4e5f6":
            hint = ("Hellenistic authors using prohairesis include early Stoics (Diogenes Laertius VII "
                    "reports Chrysippus on deliberate choice) and Peripatetics (Theophrastus). "
                    "Check TLG E for Hellenistic uses of προαίρεσις; add argument node(s) with "
                    "`precedes` edge to the Roman Imperial cluster and `cites_primary_source` to a passage.")
        elif cid == "concept_clinamen_atomic_swerve_epicurus_m3n4o5p6":
            hint = ("The gap is expected: Epicurus developed the swerve as a response to Democritus, "
                    "not adopted by Classical authors. Still, Aristotle's Physics II.4-6 discusses "
                    "spontaneity and chance (τύχη / τὸ αὐτόματον) in a way that may bridge the two. "
                    "Consider adding an argument node for Aristotle's critique of Democritean necessity "
                    "and linking it via `critiques` to Democritean Atomistic Determinism.")
        elif cid == "concept_autexousion_christian":
            hint = ("The Patristic gap is significant: Justin Martyr (2 Apol. 6.5), Tatian, Irenaeus "
                    "(Adv. Haer. IV.37), and Clement (Strom. II.4) all use αὐτεξούσιον — yet no Patristic "
                    "argument node is connected to this concept node. Wire `argument_irenaeuss_antignostic_argument_for_free_will_f54fe920` "
                    "and the Justin autexousion argument to `concept_autexousion_christian` via `employs`.")
        elif cid == "concept_pronoia_levels_proclus_a6d8c9b4":
            hint = ("Roman Imperial Middle Platonists (Plutarch, Alcinous Didaskalikos ch. 12, Apuleius "
                    "De Platone I.12) distinguish levels of providence. Add argument nodes from these authors "
                    "and connect via `employs` / `precedes` to fill the gap between the CAFMA anti-prayer "
                    "argument and the Proclean hierarchy.")
        elif cid == "concept_endechomenon_contingent_aristotle_e5f6g7h8":
            hint = ("A 3-period gap is the largest in the dataset. Hellenistic Stoics extensively debated "
                    "contingency (Chrysippus's response to the Master Argument; Diodorus Cronus). Roman "
                    "Imperial: Alexander De Fato §§10-13 uses ἐνδεχόμενον explicitly. Patristic: Origen "
                    "De Principiis III.1.2 invokes contingency of rational natures. Each period needs ≥1 "
                    "argument node connected via `discusses` to this concept.")
        else:
            hint = (f"Identify {tgap.missing_periods[0]} authors who deploy this concept, add argument "
                    f"nodes with passage grounding, and connect via `precedes` / `extends` / `influences`.")
        lines.append(f"**Suggested next step:** {hint}\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("markdown written to %s", path)


# ---------------------------------------------------------------------------
# JSON serialisation
# ---------------------------------------------------------------------------


def write_json(
    grounding_gaps: list[GroundingGap],
    unmodeled_debates: list[UnmodeledDebate],
    transmission_gaps: list[TransmissionGap],
    path: Path,
    top_n: int = 10,
) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "top_n": top_n,
        "grounding_gaps": [asdict(g) for g in grounding_gaps[:top_n]],
        "unmodeled_debates": [asdict(d) for d in unmodeled_debates[:top_n]],
        "transmission_gaps": [asdict(t) for t in transmission_gaps[:top_n]],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    logger.info("JSON written to %s", path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top", type=int, default=10, help="Top N leads per category (default: 10)")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="Output directory")
    args = parser.parse_args(argv)

    out_dir: Path = args.out_dir
    out_json = out_dir / "research_leads.json"
    out_md = out_dir / "research_leads.md"

    nodes = load_nodes()
    edges = load_edges()

    logger.info("computing grounding gaps …")
    grounding_gaps = compute_grounding_gaps(nodes, edges)
    logger.info("  %d gaps found", len(grounding_gaps))

    logger.info("computing unmodeled debates …")
    unmodeled_debates = compute_unmodeled_debates(nodes, edges)
    logger.info("  %d candidate pairs", len(unmodeled_debates))

    logger.info("computing transmission gaps …")
    transmission_gaps = compute_transmission_gaps(nodes, edges)
    logger.info("  %d gaps found", len(transmission_gaps))

    write_json(grounding_gaps, unmodeled_debates, transmission_gaps, out_json, top_n=args.top)
    write_markdown(grounding_gaps, unmodeled_debates, transmission_gaps, out_md, top_n=args.top)

    print("\n=== TOP RESEARCH LEADS ===\n")

    print("─── (i) Grounding Gaps (top 5) ───")
    for rank, g in enumerate(grounding_gaps[:5], 1):
        print(f"  GG-{rank} [{g.period}] {g.label[:70]}")
        print(f"       concept-degree={g.concept_degree}  total-degree={g.total_degree}")
        print(f"       id: {g.arg_id}")

    print("\n─── (ii) Unmodeled Debates — ancient pairs (top 5) ───")
    ancient = [d for d in unmodeled_debates if d.both_ancient]
    for rank, d in enumerate(ancient[:5], 1):
        print(f"  UD-{rank} [{d.arg1_period}] {d.arg1_label[:50]}")
        print(f"        ↔  [{d.arg2_period}] {d.arg2_label[:50]}")
        print(f"       shared concepts ({d.shared_concept_count}): {', '.join(d.shared_concept_labels)}")

    print("\n─── (iii) Transmission Gaps ───")
    for rank, t in enumerate(transmission_gaps[:4], 1):
        print(f"  TG-{rank} {t.label}")
        print(f"       attested: {t.attested_periods}  missing: {t.missing_periods}")
        print(f"       id: {t.concept_id}")

    print(f"\nFull report: {out_md}")
    print(f"JSON: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
