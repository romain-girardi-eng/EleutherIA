#!/usr/bin/env python3
"""Separate three Bobzien works and repair their scholarly-claim provenance.

The current KG conflates Bobzien's 2013 OSAP article, her 2014 chapter in
``What Is Up to Us?``, and her different 2014 Cambridge Companion chapter.  It
also repeats the very "say yes / say no" translation that the first two works
reject.  This dry-run-by-default wave creates distinct publication and argument
nodes, removes two unrelated auto-wired edges, corrects the edited-volume
metadata, and gives every new scholarly claim an exact source node and pages.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
import uuid
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = ROOT / "data"
STAMP = "bobzien_bibliography_repair_2026_08_24"
NOW = "2026-08-24 00:00:00+00:00"

BOBZIEN = "person_bobzien_susanne_contemporary"
ARISTOTLE = "person_aristotle_384_322bce_c2d4f6a8"
NE_WORK = "work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9"
PASSAGE_1113 = "passage_aristotle_en_iii_5_1113b7"
PASSAGE_1114 = "passage_aristotle_en_iii_5_1114b1"
PASSAGE_PROHAIRESIS = "passage_arist_en_3_2"
DESTREE_VOLUME = "pub_destree_salles_zingano_2014_what_is_up_to_us"
POLANSKY_CHAPTER = "pub_bobzien_2014_choice_responsibility"
EXISTING_DESTREE_ARGUMENT = (
    "argument_bobzien_2014_aristotle_en_iii_1113b_anti_indeterminist"
)
TWO_SIDEDNESS = "concept_two_sidedness_eph_hemin"

PUB_2013 = "pub_bobzien_2013_found_in_translation"
PUB_2014_DESTREE = "pub_bobzien_2014_aristotle_ne_1113b7_8_free_choice"
ARG_2013_VICE_VERSA = "argument_bobzien_2013_1113b7_8_vice_versa_translation"
ARG_2013_RECEPTION = "argument_bobzien_2013_saying_no_reception_history"
ARG_2014_CHARACTER = "argument_bobzien_2014_character_causes_noble_base_action"
ARG_2014_ALTERNATIVES = "argument_bobzien_2014_alternatives_without_indeterminism"
ARG_2014_PROHAIRESIS = "argument_bobzien_2014_prohairesis_not_free_faculty"
ARG_2014_DISPOSITIONS = "argument_bobzien_2014_indirect_voluntariness_dispositions"

NEW_NODE_IDS = {
    PUB_2013,
    PUB_2014_DESTREE,
    ARG_2013_VICE_VERSA,
    ARG_2013_RECEPTION,
    ARG_2014_CHARACTER,
    ARG_2014_ALTERNATIVES,
    ARG_2014_PROHAIRESIS,
    ARG_2014_DISPOSITIONS,
}

WRONG_EDGE_IDS = {
    "571e7b16-9823-46f4-bd35-d28f44c2a2d5",
    "b9aa058c-7da9-47fb-9732-5cfbc3391838",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "")


def metadata(obj: dict[str, Any]) -> dict[str, Any]:
    value = obj.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return {}
    return copy.deepcopy(value) if isinstance(value, dict) else {}


def set_metadata(obj: dict[str, Any], value: dict[str, Any]) -> None:
    if isinstance(obj.get("metadata"), str):
        obj["metadata"] = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        obj["metadata"] = value


def require_node(by_node: dict[str, dict[str, Any]], wanted: str) -> dict[str, Any]:
    if wanted not in by_node:
        raise RuntimeError(f"required KG node missing: {wanted}")
    return by_node[wanted]


def make_node(
    wanted: str,
    *,
    label: str,
    description: str,
    node_type: str,
    node_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "alternative_names": "[]",
        "created_at": NOW,
        "description": description,
        "id": wanted,
        "label": label,
        "metadata": {STAMP: True, **node_metadata},
        "node_id": wanted,
        "period": "Contemporary",
        "role": None,
        "school": None,
        "type": node_type,
        "updated_at": NOW,
    }


def edge_id(source: str, relation: str, target: str) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"https://eleutheria.example/kg/edge/{source}/{relation}/{target}",
        )
    )


def make_edge(
    source: str,
    relation: str,
    target: str,
    *,
    note: str,
    confidence: float = 1.0,
) -> dict[str, Any]:
    return {
        "confidence": confidence,
        "created_at": NOW,
        "edge_id": edge_id(source, relation, target),
        "metadata": {
            STAMP: True,
            "auto_generated": False,
            "confidence": confidence,
            "note": note,
        },
        "relation": relation,
        "source": source,
        "source_id": source,
        "target": target,
        "target_id": target,
        "weight": confidence,
    }


def source_checked_metadata(
    scholarly_work_id: str, page_range: str, claim_pages: str, source_note: str
) -> dict[str, Any]:
    return {
        "attestation_type": "attributed_scholarly_interpretation",
        "citation_verdict": "source_checked",
        "citation_verified": True,
        "claim_pages": claim_pages,
        "independent_human_verification_required": True,
        "page_range": page_range,
        "scholarly_work_id": scholarly_work_id,
        "source_note": source_note,
        "verification_status": "double_agent_source_checked_pending_human_signoff",
    }


def new_nodes() -> list[dict[str, Any]]:
    publication_2013 = make_node(
        PUB_2013,
        label="Found in Translation: Aristotle’s Nicomachean Ethics 3.5, 1113b7–8, and Its Reception",
        description=(
            "Susanne Bobzien’s 2013 study of the Greek text and reception of "
            "Nicomachean Ethics III.5, 1113b7–8. It distinguishes the sentence’s "
            "vice-versa syntax about acting and not acting from the later ‘saying "
            "no / saying yes’ translation tradition, and traces that mistranslation’s "
            "reception."
        ),
        node_type="publication",
        node_metadata={
            "author": "Susanne Bobzien",
            "container_title": "Oxford Studies in Ancient Philosophy",
            "doi": "10.1093/acprof:oso/9780199679430.003.0004",
            "editor": "Brad Inwood",
            "isbn": "9780199679430",
            "pages": "103-148",
            "part": "2",
            "publisher": "Oxford University Press",
            "publication_date": "2013-11-28",
            "type": "chapter_in_serial_volume",
            "verification_sources": [
                "Crossref DOI record",
                "Oxford Academic, Oxford Studies in Ancient Philosophy, Volume 45",
                "author preprint visually checked (48 physical pages)",
            ],
            "volume": "45",
            "year": 2013,
        },
    )
    publication_2014 = make_node(
        PUB_2014_DESTREE,
        label="Aristotle’s Nicomachean Ethics 1113b7–8 and Free Choice",
        description=(
            "Susanne Bobzien’s chapter in What Is Up to Us? argues, by close "
            "linguistic and contextual analysis, that EN III.5, 1113b7–8 concerns "
            "acting and refraining from acting, not acts of saying yes or no, and "
            "does not provide evidence for causally indeterminist choice."
        ),
        node_type="publication",
        node_metadata={
            "author": "Susanne Bobzien",
            "booktitle": "What Is Up to Us? Studies on Agency and Responsibility in Ancient Philosophy",
            "editors": ["Pierre Destrée", "Ricardo Salles", "Marco Zingano"],
            "isbn": "9783896656346",
            "later_reprint": {
                "book": "Determinism, Freedom, and Moral Responsibility",
                "doi": "10.1093/oso/9780198866732.003.0004",
                "pages": "77-92",
                "publisher": "Oxford University Press",
                "year": 2021,
            },
            "original_doi": None,
            "pages": "59-73",
            "publisher": "Academia Verlag",
            "publisher_location": "Sankt Augustin",
            "series": "Studies in Ancient Moral and Political Philosophy 1",
            "type": "chapter",
            "verification_sources": [
                "publisher table of contents PDF",
                "author manuscript visually checked (15 physical pages; printed 59-73)",
                "WorldCat OCLC 900924278",
            ],
            "year": 2014,
        },
    )

    argument_2013_vice_versa = make_node(
        ARG_2013_VICE_VERSA,
        label="Bobzien 2013 — the vice-versa syntax of EN III.5, 1113b7–8",
        description=(
            "Bobzien argues that the second half of EN III.5, 1113b7–8 is "
            "elliptical and supplies ‘to act’, yielding a vice-versa relation: where "
            "acting is up to us, not acting is up to us, and where not acting is up "
            "to us, acting is up to us. No verb of saying occurs in the Greek."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            PUB_2013,
            "103-148",
            "author-preprint physical pp. 8-15; printed-page subrange not asserted",
            "Bobzien 2013, Part I; page-map differs from the printed OSAP setting.",
        ),
    )
    argument_2013_reception = make_node(
        ARG_2013_RECEPTION,
        label="Bobzien 2013 — reception history of the ‘saying-no’ mistranslation",
        description=(
            "Bobzien treats the ‘saying no / saying yes’ wording as a reception "
            "phenomenon rather than Aristotle’s wording. She finds no ancient or "
            "Latin-medieval precedent for that interpretation, examines the Arabic "
            "transmission and its lacuna, and traces the modern translation tradition "
            "that made the wording influential."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            PUB_2013,
            "103-148",
            "author-preprint physical pp. 18-40; printed-page subrange not asserted",
            "Bobzien 2013, Part II; claim is explicitly about reception, not ancient attestation.",
        ),
    )
    argument_2014_character = make_node(
        ARG_2014_CHARACTER,
        label="Bobzien 2014 — character as causal ground of responsibility for noble/base action",
        description=(
            "Bobzien reads the primary purpose of NE III.1–5 as explaining why "
            "agents are responsible for actions qua noble or base: typically through "
            "choice, the agent’s character disposition is a causal factor of the action."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            POLANSKY_CHAPTER, "81-109", "82, 97-101", "Cambridge chapter PDF, printed pages."
        ),
    )
    argument_2014_alternatives = make_node(
        ARG_2014_ALTERNATIVES,
        label="Bobzien 2014 — alternatives without causal indeterminism",
        description=(
            "Bobzien argues that Aristotelian deliberation presupposes alternative "
            "options and awareness of them, but this entails neither that the agent’s "
            "action is causally undetermined nor that the agent believes it is. The "
            "two-sided formulations at EN 1113b7–8 and 1113b30–33 therefore do not "
            "establish indeterminist freedom to do otherwise."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            POLANSKY_CHAPTER, "81-109", "90-93, 106", "Cambridge chapter PDF, printed pages."
        ),
    )
    argument_2014_prohairesis = make_node(
        ARG_2014_PROHAIRESIS,
        label="Bobzien 2014 — prohairesis is not a free decision or faculty",
        description=(
            "Bobzien argues that prohairesis in NE III.1–5 is a deliberated desire "
            "with duration, not an act of deciding between alternatives. Neither it "
            "nor the judgment that co-causes it is a faculty for causally undetermined "
            "choice, decision, or free will."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            POLANSKY_CHAPTER, "81-109", "93-94", "Cambridge chapter PDF, printed pages."
        ),
    )
    argument_2014_dispositions = make_node(
        ARG_2014_DISPOSITIONS,
        label="Bobzien 2014 — indirect voluntariness of character dispositions",
        description=(
            "Bobzien reconstructs virtues and vices as indirectly voluntary: they "
            "are foreseeable consequences of repeated voluntary actions whose origin "
            "lies in the agent. Unlike a directly voluntary action, a disposition "
            "cannot normally be ended immediately by reversing one’s desire; "
            "reversibility is not a condition of responsibility."
        ),
        node_type="argument",
        node_metadata=source_checked_metadata(
            POLANSKY_CHAPTER, "81-109", "105-109", "Cambridge chapter PDF, printed pages."
        ),
    )
    return [
        publication_2013,
        publication_2014,
        argument_2013_vice_versa,
        argument_2013_reception,
        argument_2014_character,
        argument_2014_alternatives,
        argument_2014_prohairesis,
        argument_2014_dispositions,
    ]


def repair_existing_nodes(by_node: dict[str, dict[str, Any]]) -> None:
    argument = require_node(by_node, EXISTING_DESTREE_ARGUMENT)
    argument["label"] = "Bobzien 2014 — EN III.5, 1113b7–8 is not evidence for indeterminist choice"
    argument["description"] = (
        "Bobzien argues that EN III.5, 1113b7–8 has an elliptical vice-versa "
        "construction: both clauses concern acting and not acting. Choice is neither "
        "expressly mentioned nor implied as the sentence’s topic, and the passage "
        "does not imply causal indeterminacy. It supplies a premise for Aristotle’s "
        "argument that virtuous and vicious action are up to us, not evidence for "
        "indeterminist free choice."
    )
    data = metadata(argument)
    data.update(
        source_checked_metadata(
            PUB_2014_DESTREE,
            "59-73",
            "author-manuscript pp. 13-15 / printed pp. 71-73",
            "Bobzien 2014, §4; publisher TOC and author manuscript checked.",
        )
    )
    data.update(
        {
            "description_en": argument["description"],
            "description_fr": (
                "Bobzien soutient que EN III.5, 1113b7–8 est une construction "
                "elliptique vice-versa portant dans les deux membres sur agir et ne "
                "pas agir. Le choix n’y est ni expressément mentionné ni impliqué "
                "comme sujet, et le passage n’implique aucune indétermination causale."
            ),
            "destree2014_chapter": "ch04",
            "destree2014_chapter_pages": "59-73",
            "merged_source_scope_corrected": True,
            STAMP: True,
        }
    )
    for key in (
        "semantic_merges_2026_08_17_chapter_synthesis",
        "description_en_pre_2026_08_16",
    ):
        data.pop(key, None)
    set_metadata(argument, data)
    argument["updated_at"] = NOW

    concept = require_node(by_node, TWO_SIDEDNESS)
    concept["description"] = (
        "A two-sided feature attributed to Aristotle’s τὸ ἐφ’ ἡμῖν: in the "
        "circumstances at issue, what is up to an agent to do is also up to the agent "
        "not to do. Susan Sauvé Meyer (2014, ch. 5, pp. 75–90) argues that this "
        "should not simply be equated with the modern Principle of Alternate "
        "Possibilities. Susanne Bobzien (2014, ch. 4, pp. 59–73) argues specifically "
        "that EN III.5, 1113b7–8 concerns acting/not acting and is no evidence for "
        "causally indeterminist choice. These are attributed scholarly readings, not "
        "an untranslated modern doctrine placed in Aristotle’s mouth."
    )
    concept_data = metadata(concept)
    concept_data.update(
        {
            "description_en": concept["description"],
            "description_fr": (
                "Trait bilatéral attribué au τὸ ἐφ’ ἡμῖν aristotélicien : dans les "
                "circonstances considérées, ce qu’il dépend de l’agent de faire, il "
                "dépend aussi de lui de ne pas le faire. Sauvé Meyer (2014, ch. 5, "
                "p. 75–90) et Bobzien (2014, ch. 4, p. 59–73) en proposent des "
                "lectures distinctes et attribuées ; aucune ne transforme le grec en "
                "un énoncé où Aristote dirait oui ou non."
            ),
            "scholarly_readings": [
                {"scholar": "Susan Sauvé Meyer", "chapter": 5, "pages": "75-90"},
                {"scholar": "Susanne Bobzien", "chapter": 4, "pages": "59-73"},
            ],
            "verified_reference": (
                "Aristotle, EN III.5 1113b7-8; Bobzien 2014, 59-73; "
                "Sauvé Meyer 2014, 75-90."
            ),
            STAMP: True,
        }
    )
    set_metadata(concept, concept_data)
    concept["updated_at"] = NOW

    polansky = require_node(by_node, POLANSKY_CHAPTER)
    polansky_data = metadata(polansky)
    polansky_data.update(
        {
            "booktitle": "The Cambridge Companion to Aristotle's Nicomachean Ethics",
            "doi": "10.1017/CCO9781139022484.005",
            "editor": "Ronald Polansky",
            "isbn": "9780521192767",
            "online_isbn": "9781139022484",
            "pages": "81-109",
            "publisher": "Cambridge University Press",
            "type": "chapter",
            "verification_sources": ["Cambridge Core", "Crossref DOI record"],
            STAMP: True,
        }
    )
    set_metadata(polansky, polansky_data)
    polansky["updated_at"] = NOW

    volume = require_node(by_node, DESTREE_VOLUME)
    volume["description"] = (
        "Edited by Pierre Destrée, Ricardo Salles and Marco Zingano, this 2014 "
        "Academia Verlag volume contains an introduction and twenty-two studies of "
        "agency and responsibility from Democritus to Simplicius. Its contributors "
        "advance materially different positions: for example Bobzien rejects EN "
        "1113b7–8 as evidence for indeterminist choice, Sauvé Meyer distinguishes "
        "what is up to us from contingency, and Echeñique explicitly combines "
        "appraisability compatibilism with accountability incompatibilism. The "
        "volume is therefore a structured scholarly debate, not a single consensus "
        "statement."
    )
    volume_data = metadata(volume)
    volume_data.update(
        {
            "chapter_count": 22,
            "contribution_count": 22,
            "description_en": volume["description"],
            "page_count": 372,
            "physical_extent": "vi, 372 pages",
            "verification_sources": [
                "Academia Verlag / C.H. Beck table of contents PDF",
                "WorldCat OCLC 900924278",
                "BMCR 2015.07.28",
            ],
            STAMP: True,
        }
    )
    volume_data.pop("key_claim", None)
    set_metadata(volume, volume_data)
    volume["updated_at"] = NOW


def build_new_edges() -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for publication in (PUB_2013, PUB_2014_DESTREE):
        edges.append(
            make_edge(publication, "authored_by", BOBZIEN, note="publication authorship")
        )
        edges.append(
            make_edge(publication, "interprets", NE_WORK, note="publication subject")
        )
        edges.append(
            make_edge(
                publication,
                "cites_primary_source",
                PASSAGE_1113,
                note="exact EN III.5 1113b7-8 locus",
            )
        )
    edges.append(
        make_edge(
            PUB_2014_DESTREE,
            "part_of",
            DESTREE_VOLUME,
            note="chapter in the 2014 edited volume, pp. 59-73",
        )
    )

    argument_sources = {
        EXISTING_DESTREE_ARGUMENT: (PUB_2014_DESTREE, PASSAGE_1113),
        ARG_2013_VICE_VERSA: (PUB_2013, PASSAGE_1113),
        ARG_2013_RECEPTION: (PUB_2013, PASSAGE_1113),
        ARG_2014_CHARACTER: (POLANSKY_CHAPTER, PASSAGE_1114),
        ARG_2014_ALTERNATIVES: (POLANSKY_CHAPTER, PASSAGE_1113),
        ARG_2014_PROHAIRESIS: (POLANSKY_CHAPTER, PASSAGE_PROHAIRESIS),
        ARG_2014_DISPOSITIONS: (POLANSKY_CHAPTER, PASSAGE_1114),
    }
    for argument, (publication, passage) in argument_sources.items():
        edges.append(
            make_edge(argument, "advanced_in", publication, note="claim source publication")
        )
        edges.append(make_edge(argument, "created_by", BOBZIEN, note="claim author"))
        edges.append(
            make_edge(
                argument,
                "cites_primary_source",
                passage,
                note="primary locus explicitly engaged by the scholarly claim",
            )
        )
    return edges


def transform(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    nodes = copy.deepcopy(nodes)
    edges = copy.deepcopy(edges)
    counts: Counter[str] = Counter()
    quarantine: list[dict[str, Any]] = []
    by_node = {node_id(node): node for node in nodes}

    for wanted in (
        BOBZIEN,
        ARISTOTLE,
        NE_WORK,
        PASSAGE_1113,
        PASSAGE_1114,
        PASSAGE_PROHAIRESIS,
        DESTREE_VOLUME,
        POLANSKY_CHAPTER,
        EXISTING_DESTREE_ARGUMENT,
        TWO_SIDEDNESS,
    ):
        require_node(by_node, wanted)

    if NEW_NODE_IDS.issubset(by_node) and all(
        metadata(by_node[wanted]).get(STAMP) is True
        for wanted in (
            EXISTING_DESTREE_ARGUMENT,
            TWO_SIDEDNESS,
            POLANSKY_CHAPTER,
            DESTREE_VOLUME,
        )
    ):
        validate(nodes, edges)
        return nodes, edges, [], counts

    for wanted in (
        EXISTING_DESTREE_ARGUMENT,
        TWO_SIDEDNESS,
        POLANSKY_CHAPTER,
        DESTREE_VOLUME,
    ):
        quarantine.append({"record_type": "kg_node_before", "record": copy.deepcopy(by_node[wanted])})
    repair_existing_nodes(by_node)
    counts["nodes_corrected"] += 4

    for node in new_nodes():
        wanted = node_id(node)
        if wanted in by_node:
            if metadata(by_node[wanted]).get(STAMP) is not True:
                raise RuntimeError(f"new node id already occupied by unrelated row: {wanted}")
            continue
        nodes.append(node)
        by_node[wanted] = node
        counts["nodes_added"] += 1

    kept_edges: list[dict[str, Any]] = []
    for edge in edges:
        if edge.get("edge_id") in WRONG_EDGE_IDS:
            quarantine.append({"record_type": "kg_edge_removed", "record": edge})
            counts["wrong_edges_removed"] += 1
            continue
        kept_edges.append(edge)
    edges = kept_edges

    triples = {
        (edge.get("source"), edge.get("relation"), edge.get("target")) for edge in edges
    }
    ids = {str(edge.get("edge_id")) for edge in edges}
    for edge in build_new_edges():
        triple = (edge["source"], edge["relation"], edge["target"])
        if triple in triples:
            continue
        if edge["edge_id"] in ids:
            raise RuntimeError(f"deterministic edge-id collision: {edge['edge_id']}")
        edges.append(edge)
        triples.add(triple)
        ids.add(edge["edge_id"])
        counts["edges_added"] += 1

    validate(nodes, edges)
    return nodes, edges, quarantine, counts


def validate(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    by_node = {node_id(node): node for node in nodes}
    missing = NEW_NODE_IDS - by_node.keys()
    if missing:
        raise RuntimeError(f"new Bobzien nodes missing: {sorted(missing)}")
    if any(edge.get("edge_id") in WRONG_EDGE_IDS for edge in edges):
        raise RuntimeError("unrelated auto-wired Bobzien edge survived")

    for wanted in (EXISTING_DESTREE_ARGUMENT, TWO_SIDEDNESS):
        haystack = json.dumps(by_node[wanted], ensure_ascii=False).lower()
        forbidden = ("say yes", "say no", "dire oui", "dire non")
        if any(term in haystack for term in forbidden):
            raise RuntimeError(f"rejected saying-no translation survives in {wanted}")

    argument_ids = {
        EXISTING_DESTREE_ARGUMENT,
        ARG_2013_VICE_VERSA,
        ARG_2013_RECEPTION,
        ARG_2014_CHARACTER,
        ARG_2014_ALTERNATIVES,
        ARG_2014_PROHAIRESIS,
        ARG_2014_DISPOSITIONS,
    }
    triples = {
        (edge.get("source"), edge.get("relation"), edge.get("target")) for edge in edges
    }
    for wanted in argument_ids:
        work = metadata(by_node[wanted]).get("scholarly_work_id")
        if not work or (wanted, "advanced_in", work) not in triples:
            raise RuntimeError(f"argument {wanted} lacks matching advanced_in provenance")
        if (wanted, "created_by", BOBZIEN) not in triples:
            raise RuntimeError(f"argument {wanted} lacks Bobzien authorship")

    if metadata(by_node[DESTREE_VOLUME]).get("contribution_count") != 22:
        raise RuntimeError("edited-volume contribution count is not 22")
    if metadata(by_node[POLANSKY_CHAPTER]).get("doi") != "10.1017/CCO9781139022484.005":
        raise RuntimeError("Cambridge chapter DOI missing or incorrect")
    if metadata(by_node[PUB_2013]).get("doi") != "10.1093/acprof:oso/9780199679430.003.0004":
        raise RuntimeError("OSAP article DOI missing or incorrect")


def write_jsonl_preserving(
    path: Path,
    rows: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], str],
) -> None:
    """Preserve untouched raw lines so a surgical repair stays reviewable."""
    originals = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    desired = {key(row): row for row in rows}
    if len(desired) != len(rows):
        raise RuntimeError(f"duplicate identity while writing {path}")
    seen: set[str] = set()
    output: list[str] = []
    for line in originals:
        old = json.loads(line)
        wanted = key(old)
        if wanted not in desired:
            continue
        new = desired[wanted]
        output.append(
            line
            if old == new
            else json.dumps(new, ensure_ascii=False, sort_keys=True)
        )
        seen.add(wanted)
    for wanted in sorted(desired.keys() - seen):
        output.append(json.dumps(desired[wanted], ensure_ascii=False, sort_keys=True))
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        tmp = Path(handle.name)
        handle.write("\n".join(output) + "\n")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    args = parser.parse_args(argv)
    if args.write and args.dry_run:
        parser.error("--write and --dry-run are mutually exclusive")

    data_root = args.data_root.expanduser().resolve()
    nodes_path = data_root / "kg/nodes.jsonl"
    edges_path = data_root / "kg/edges.jsonl"
    nodes = read_jsonl(nodes_path)
    edges = read_jsonl(edges_path)
    new_node_rows, new_edge_rows, quarantine, counts = transform(nodes, edges)

    print("Bobzien bibliography and claim repair")
    print("mode:", "WRITE" if args.write else "DRY-RUN")
    for name, count in sorted(counts.items()):
        print(f"{name}: {count}")
    print(f"rows: nodes {len(nodes)}->{len(new_node_rows)}, edges {len(edges)}->{len(new_edge_rows)}")
    print("quarantine records:", len(quarantine))
    if not args.write:
        print("dry-run: nothing written (use --write to apply)")
        return 0
    if not counts:
        print("already applied: no files written")
        return 0

    write_jsonl_preserving(nodes_path, new_node_rows, node_id)
    write_jsonl_preserving(edges_path, new_edge_rows, lambda edge: str(edge.get("edge_id") or ""))
    quarantine_path = data_root / "audit/2026-08-24_bobzien_bibliography_quarantine.jsonl"
    quarantine_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in quarantine),
        encoding="utf-8",
    )
    print("wrote:", nodes_path, edges_path, quarantine_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
