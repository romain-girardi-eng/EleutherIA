#!/usr/bin/env python3
"""
Apply the first reviewed manual KG provenance fixes without generating content.

This script only:
- updates reviewed node labels/descriptions/metadata
- creates verified source work nodes when needed
- adds reviewed `source_for` / `contains` / `authored_by` edges
- removes clearly unsupported reviewed edges
- adds passage citations tied to existing passages in the corpus

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/apply_manual_review_batch_01.py
    uv run --directory database python database/scripts/apply_manual_review_batch_01.py --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "free_will"
RUN_TAG = "kg_manual_review_batch_01_2026_03_08"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-08-kg-manual-review-batch-01-results.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-08-kg-manual-review-batch-01-results.md"


def jd(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class NodeUpdate:
    node_id: str
    label: str
    description: str
    metadata: dict[str, Any]
    alternative_names: list[str] | None = None


@dataclass(frozen=True)
class WorkNode:
    node_id: str
    label: str
    period: str
    description: str
    metadata: dict[str, Any]
    author_person_id: str


@dataclass(frozen=True)
class EdgeSpec:
    source_id: str
    target_id: str
    relation: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class CitationSpec:
    kg_node_id: str
    passage_id: str
    citation_type: str
    confidence: float
    notes: str


NODE_UPDATES = [
    NodeUpdate(
        node_id="argument_aristotles_potentialityactuality_argument_20c5ac91",
        label="Aristotle's Potentiality-Actuality Argument",
        description=(
            "Aristotle distinguishes potentiality from actuality and argues against the "
            "Megarian claim that a thing has a capacity only when it is actually exercising "
            "it. In Metaphysics IX.3-4 he treats unexercised capacities as real and uses them "
            "to explain possibility and change."
        ),
        metadata={
            "formulator": "Aristotle",
            "argument_type": "metaphysical distinction between potentiality and actuality",
            "source_work": "Metaphysics IX (Theta)",
            "primary_source": "Aristotle, Metaphysics IX.3-4",
            "ancient_sources": [
                "Aristotle, Metaphysics IX.3",
                "Aristotle, Metaphysics IX.4",
            ],
        },
    ),
    NodeUpdate(
        node_id="argument_aristotle_event_taxonomy",
        label="Aristotelian Event Taxonomy (via Alexander De Fato)",
        description=(
            "In De Fato 4-5 Alexander of Aphrodisias presents an Aristotelian division between "
            "events with no end and events for an end; among the latter he distinguishes natural "
            "processes, rational or deliberate production, and chance or automatic outcomes. "
            "Alexander uses this scheme to argue that fate belongs with what occurs by nature, "
            "not with what proceeds from rational choice."
        ),
        metadata={
            "formulator": "Aristotle (reported by Alexander of Aphrodisias)",
            "argument_type": "classification of events and causes",
            "source_work": "Alexander of Aphrodisias, De Fato; Aristotle, Physics II",
            "primary_source": "Alexander of Aphrodisias, De Fato 4-5",
            "scholarly_status": (
                "editorial label for a classification reported in Alexander of Aphrodisias, "
                "De Fato 4-5"
            ),
            "ancient_sources": [
                "Alexander of Aphrodisias, De Fato 4-5",
                "Aristotle, Physics II.4-6",
            ],
            "used_by": ["Alexander of Aphrodisias"],
        },
    ),
    NodeUpdate(
        node_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        label="Aristotle's Voluntary Action Argument (Eph' Hemin)",
        description=(
            "In Nicomachean Ethics III.1 Aristotle distinguishes voluntary from involuntary "
            "action by reference to internal origin and knowledge of particulars; in III.5 he "
            "adds that virtue and vice are 'up to us'. Together these chapters ground "
            "Aristotle's account of praise, blame, and responsibility."
        ),
        metadata={
            "formulator": "Aristotle",
            "argument_type": "analysis of voluntary action and responsibility",
            "source_work": "Nicomachean Ethics III.1-5",
            "primary_source": "Aristotle, Nicomachean Ethics III.1; III.5",
            "ancient_sources": [
                "Aristotle, Nicomachean Ethics III.1",
                "Aristotle, Nicomachean Ethics III.5",
            ],
        },
    ),
    NodeUpdate(
        node_id="argument_platos_laws_x_selfmotion_argument_8c31a166",
        label="Plato's Laws X Self-Motion Argument",
        description=(
            "In Laws X Plato argues that soul, as the self-moving source of motion, is prior to "
            "body and is responsible for the ordered motions of the cosmos. The argument is part "
            "of Book X's reply to impiety and atheism."
        ),
        metadata={
            "formulator": "Plato",
            "argument_type": "argument that soul as self-mover is prior to body",
            "source_work": "Laws X",
            "primary_source": "Plato, Laws X 891e-899d",
            "ancient_sources": ["Plato, Laws X 891e-899d"],
        },
    ),
    NodeUpdate(
        node_id="argument_sea_battle_aristotle_f6g7h8i9",
        label="Sea Battle Argument (Future Contingents)",
        description=(
            "In De Interpretatione 9 Aristotle addresses future contingent statements such as "
            "whether there will be a sea battle tomorrow. He argues that while the disjunction "
            "is necessary, it does not follow that either outcome is individually necessary in "
            "advance; this text became central to later debates about future contingents."
        ),
        metadata={
            "formulator": "Aristotle",
            "argument_type": "future contingents",
            "source_work": "De Interpretatione 9",
            "primary_source": "Aristotle, De Interpretatione 9.2; 9.15",
            "scholarly_status": (
                "standard later label based on Aristotle's sea-battle example in "
                "De Interpretatione 9"
            ),
            "ancient_sources": [
                "Aristotle, De Interpretatione 9.2",
                "Aristotle, De Interpretatione 9.15",
            ],
        },
    ),
    NodeUpdate(
        node_id="argument_the_practical_syllogism_1d2e7506",
        label="The Practical Syllogism",
        description=(
            "Aristotle's account of practical reasoning connects thought about an end with "
            "desire and action. In De Anima III.10 and Nicomachean Ethics VII.3 practical "
            "intellect is oriented toward action rather than contemplation, and action issues "
            "when thought and desire converge without impediment."
        ),
        metadata={
            "formulator": "Aristotle",
            "argument_type": "practical reasoning and action",
            "source_work": "De Anima III.10; Nicomachean Ethics VII.3",
            "primary_source": "Aristotle, De Anima III.10; Nicomachean Ethics VII.3",
            "scholarly_status": (
                "standard modern label for Aristotle's account of practical reasoning"
            ),
            "ancient_sources": [
                "Aristotle, De Anima III.10",
                "Aristotle, Nicomachean Ethics VII.3",
            ],
        },
    ),
    NodeUpdate(
        node_id="argument_two_way_powers_aristotle_i9j0k1l2",
        label="Two-Way Powers (Rational Potentialities) Argument",
        description=(
            "In Metaphysics IX Aristotle distinguishes non-rational powers, each ordered to one "
            "effect, from rational powers, which are of opposites. In IX.5 he adds that the "
            "exercise of rational powers depends on desire or choice, making this distinction "
            "important for later debates about agency."
        ),
        metadata={
            "formulator": "Aristotle",
            "argument_type": "rational vs non-rational potentialities",
            "source_work": "Metaphysics IX (Theta)",
            "primary_source": "Aristotle, Metaphysics IX.2; IX.5",
            "scholarly_status": (
                "standard later label for Aristotle's distinction between rational and "
                "non-rational powers"
            ),
            "ancient_sources": [
                "Aristotle, Metaphysics IX.2",
                "Aristotle, Metaphysics IX.5",
            ],
        },
    ),
    NodeUpdate(
        node_id="argument_frankfurt_cases_1o2p3q4r",
        label="Frankfurt Cases",
        description=(
            "Frankfurt's 1969 article presents cases in which an agent is morally responsible "
            "even though a counterfactual intervener ensures that no alternative outcome was "
            "available. These cases are designed to challenge the Principle of Alternative "
            "Possibilities."
        ),
        metadata={
            "formulator": "Harry G. Frankfurt",
            "argument_type": "counterexample to the Principle of Alternative Possibilities",
            "source_work": "Alternate Possibilities and Moral Responsibility",
            "primary_source": (
                "Harry G. Frankfurt, Alternate Possibilities and Moral Responsibility (1969)"
            ),
            "scholarly_status": (
                "standard later label for the cases introduced in Frankfurt's 1969 article"
            ),
        },
    ),
    NodeUpdate(
        node_id="argument_argument_from_animal_rationality_4629e983",
        label="Bayle's Rorarius Challenge from Animal Rationality",
        description=(
            "In the 'Rorarius' article of the Dictionnaire historique et critique, Bayle uses "
            "the problem of animal rationality to press difficulties for accounts that sharply "
            "separate human rational freedom from animal behavior. The entry functions as a "
            "skeptical challenge rather than a settled positive theory of freedom."
        ),
        metadata={
            "formulator": "Pierre Bayle",
            "argument_type": "skeptical challenge from animal rationality",
            "source_work": 'Dictionnaire historique et critique, article "Rorarius"',
            "primary_source": (
                'Pierre Bayle, Dictionnaire historique et critique, article "Rorarius" '
                "(2nd ed., 1702)"
            ),
            "edition": "second edition",
        },
        alternative_names=["Rorarius Problem"],
    ),
    NodeUpdate(
        node_id="argument_best_of_all_possible_worlds_cb9e1741",
        label="Leibniz's Best of All Possible Worlds Argument",
        description=(
            "In the Théodicée Leibniz argues that a perfectly wise and good God creates the "
            "best among possible worlds. The argument links divine choice, contingency, and "
            "freedom by distinguishing what is morally best from what is metaphysically "
            "necessary."
        ),
        metadata={
            "formulator": "Gottfried Wilhelm Leibniz",
            "argument_type": "theodicy / best possible world",
            "source_work": (
                "Essais de Théodicée sur la bonté de Dieu, la liberté de l'homme et "
                "l'origine du mal"
            ),
            "primary_source": (
                "G. W. Leibniz, Essais de Théodicée sur la bonté de Dieu, la liberté "
                "de l'homme et l'origine du mal (1710)"
            ),
        },
    ),
]

NEW_WORKS = [
    WorkNode(
        node_id="work_frankfurt_alternate_possibilities_1969",
        label="Alternate Possibilities and Moral Responsibility",
        period="Contemporary",
        description=(
            "Harry G. Frankfurt, 'Alternate Possibilities and Moral Responsibility,' The "
            "Journal of Philosophy 66.23 (December 1969), 829-839."
        ),
        metadata={
            "type": "article",
            "year": 1969,
            "author": "Harry G. Frankfurt",
            "journal": "The Journal of Philosophy",
            "volume": 66,
            "issue": 23,
            "pages": "829-839",
            "doi": "10.2307/2023833",
            "reference_url": "https://www.pdcnet.org/jphil/content/jphil_1969_0066_0023_0829_0839%26gt",
            "verified_by": RUN_TAG,
        },
        author_person_id="person_frankfurt_harry_1929_2023",
    ),
    WorkNode(
        node_id="work_bayle_rorarius_1702",
        label='Dictionnaire historique et critique, article "Rorarius"',
        period="Early Modern",
        description=(
            'Article "Rorarius" in Pierre Bayle\'s Dictionnaire historique et critique. '
            "ARTFL documents the Dictionnaire's first edition (1697) and second edition "
            "(1702); recent scholarship identifies note L of the 'Rorarius' article in the "
            "second edition as a key Bayle-Leibniz locus."
        ),
        metadata={
            "type": "dictionary article",
            "year": 1702,
            "edition": "second edition",
            "author": "Pierre Bayle",
            "parent_work": "Dictionnaire historique et critique",
            "article": "Rorarius",
            "reference_url": "https://artfl-project.uchicago.edu/dictionnaire-de-bayle",
            "secondary_reference_url": "https://periodicos.unb.br/index.php/fmc/article/view/12564",
            "verified_by": RUN_TAG,
        },
        author_person_id="person_pierre_bayle_701cb0a7",
    ),
    WorkNode(
        node_id="work_leibniz_theodicee_1710",
        label=(
            "Essais de Théodicée sur la bonté de Dieu, la liberté de l'homme et "
            "l'origine du mal"
        ),
        period="Early Modern",
        description=(
            "G. W. Leibniz's 1710 Théodicée, the work in which he presents the best-of-all-"
            "possible-worlds thesis in the context of divine justice, freedom, and evil."
        ),
        metadata={
            "type": "book",
            "year": 1710,
            "author": "Gottfried Wilhelm Leibniz",
            "short_title": "Théodicée",
            "reference_url": "https://www.gutenberg.org/files/17147/17147-h/17147-h.htm",
            "secondary_reference_url": "https://www.britannica.com/topic/Theodicy",
            "verified_by": RUN_TAG,
        },
        author_person_id="person_gottfried_leibniz_0r4m5n13",
    ),
]

EDGES_TO_ENSURE = [
    EdgeSpec(
        source_id="work_metaphysics_theta_aristotle_c350bce_f5g7h9i1",
        target_id="argument_aristotles_potentialityactuality_argument_20c5ac91",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_metaphysics_theta_aristotle_c350bce_f5g7h9i1",
        target_id="argument_aristotles_potentialityactuality_argument_20c5ac91",
        relation="source_for",
        metadata={"reference": "IX.3-4", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        target_id="argument_aristotle_event_taxonomy",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        target_id="argument_aristotle_event_taxonomy",
        relation="source_for",
        metadata={"reference": "4-5", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        target_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        target_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        relation="source_for",
        metadata={"reference": "III.1, III.5", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="passage_arist_en_3_1",
        target_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        relation="source_for",
        metadata={"reference": "III.1", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="passage_arist_en_3_5",
        target_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        relation="source_for",
        metadata={"reference": "III.5", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_laws_plato_c350bce_d4e5f6g7",
        target_id="argument_platos_laws_x_selfmotion_argument_8c31a166",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_laws_plato_c350bce_d4e5f6g7",
        target_id="argument_platos_laws_x_selfmotion_argument_8c31a166",
        relation="source_for",
        metadata={"reference": "X 891e-899d", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_de_interpretatione_aristotle_c350bce_e4f6g8h0",
        target_id="argument_sea_battle_aristotle_f6g7h8i9",
        relation="source_for",
        metadata={"reference": "9.2, 9.15", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        target_id="argument_the_practical_syllogism_1d2e7506",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_nicomachean_ethics_aristotle_c350bce_d3e5f7b9",
        target_id="argument_the_practical_syllogism_1d2e7506",
        relation="source_for",
        metadata={"reference": "VII.3", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_metaphysics_theta_aristotle_c350bce_f5g7h9i1",
        target_id="argument_two_way_powers_aristotle_i9j0k1l2",
        relation="source_for",
        metadata={"reference": "IX.2, IX.5", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_frankfurt_alternate_possibilities_1969",
        target_id="argument_frankfurt_cases_1o2p3q4r",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_frankfurt_alternate_possibilities_1969",
        target_id="argument_frankfurt_cases_1o2p3q4r",
        relation="source_for",
        metadata={"reference": "1969 article", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_bayle_rorarius_1702",
        target_id="argument_argument_from_animal_rationality_4629e983",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_bayle_rorarius_1702",
        target_id="argument_argument_from_animal_rationality_4629e983",
        relation="source_for",
        metadata={"reference": 'article "Rorarius"', "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_leibniz_theodicee_1710",
        target_id="argument_best_of_all_possible_worlds_cb9e1741",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_leibniz_theodicee_1710",
        target_id="argument_best_of_all_possible_worlds_cb9e1741",
        relation="source_for",
        metadata={"reference": "1710 Theodicy", "reviewed_by": RUN_TAG},
    ),
]

for work in NEW_WORKS:
    EDGES_TO_ENSURE.append(
        EdgeSpec(
            source_id=work.node_id,
            target_id=work.author_person_id,
            relation="authored_by",
            metadata={"reviewed_by": RUN_TAG},
        )
    )

EDGES_TO_DELETE = [
    EdgeSpec(
        source_id="argument_platos_laws_x_selfmotion_argument_8c31a166",
        target_id="concept_agent_causation_0l4g5h13",
        relation="discusses",
        metadata={},
    ),
    EdgeSpec(
        source_id="argument_platos_laws_x_selfmotion_argument_8c31a166",
        target_id="concept_tripartite_soul_plato_e5f6g7h8",
        relation="employs",
        metadata={},
    ),
    EdgeSpec(
        source_id="argument_frankfurt_cases_1o2p3q4r",
        target_id="person_kane_robert_1938_2022",
        relation="discusses",
        metadata={},
    ),
    EdgeSpec(
        source_id="argument_argument_from_animal_rationality_4629e983",
        target_id="concept_libertas_indifferentiae_4f8a9b57",
        relation="critiques",
        metadata={},
    ),
    EdgeSpec(
        source_id="argument_argument_from_animal_rationality_4629e983",
        target_id="concept_agent_causation_0l4g5h13",
        relation="discusses",
        metadata={},
    ),
]

CITATIONS_TO_ENSURE = [
    CitationSpec(
        kg_node_id="argument_aristotles_potentialityactuality_argument_20c5ac91",
        passage_id="dd4218ff-3741-454b-a2b8-eb95c5279b0c",
        citation_type="primary_source",
        confidence=0.98,
        notes="Metaphysics IX.3 explicitly reports and rejects the Megarian thesis that one can act only when actually acting.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotles_potentialityactuality_argument_20c5ac91",
        passage_id="6f1551b9-628b-4159-a1a2-236e0dbf2d2e",
        citation_type="primary_source",
        confidence=0.96,
        notes="Metaphysics IX.4 argues that something can be possible without ever being actualized.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotle_event_taxonomy",
        passage_id="00d56f51-a218-4ec0-8899-02f34d6d76a7",
        citation_type="primary_source",
        confidence=0.88,
        notes="Physics II.4 introduces chance and the automatic as causes requiring classification.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotle_event_taxonomy",
        passage_id="44e5a1bf-e3cf-427b-b766-023e122c7e7e",
        citation_type="primary_source",
        confidence=0.92,
        notes="Physics II.5 distinguishes events for an end from what occurs by necessity or for the most part.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotle_event_taxonomy",
        passage_id="b4803598-e360-4ba4-bb0f-3f4d06cc0068",
        citation_type="primary_source",
        confidence=0.92,
        notes="Physics II.6 distinguishes chance from the broader automatic and ties chance to choice.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotle_event_taxonomy",
        passage_id="fe6fc065-9a84-4664-9630-752bc1c6bcad",
        citation_type="primary_source",
        confidence=0.97,
        notes="De Fato 4 gives Alexander's Aristotelian division between non-purposive, natural or rational, and chance cases.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotle_event_taxonomy",
        passage_id="b6c318f2-8577-49ee-8a73-26315325cccf",
        citation_type="primary_source",
        confidence=0.97,
        notes="De Fato 5 places fate with what occurs by nature rather than with what is up to rational choice.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        passage_id="61f93a32-769e-498b-968d-de545a9bd124",
        citation_type="primary_source",
        confidence=0.97,
        notes="EN III.1 defines voluntary and involuntary action by origin and knowledge of particulars.",
    ),
    CitationSpec(
        kg_node_id="argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
        passage_id="28b16b62-34cb-4db0-a445-c778d696cb4e",
        citation_type="primary_source",
        confidence=0.98,
        notes="EN III.5 states that where acting is up to us, not acting is also up to us.",
    ),
    CitationSpec(
        kg_node_id="argument_sea_battle_aristotle_f6g7h8i9",
        passage_id="6369d504-64ff-4db7-a6c0-57e413741c08",
        citation_type="primary_source",
        confidence=0.98,
        notes="De Interpretatione 9.2 gives the fatalist argument from future truth values and the sea-battle example.",
    ),
    CitationSpec(
        kg_node_id="argument_sea_battle_aristotle_f6g7h8i9",
        passage_id="308545cd-af53-43de-83ed-104be7feb9da",
        citation_type="primary_source",
        confidence=0.98,
        notes="De Interpretatione 9.15 distinguishes the necessary disjunction from the non-necessary disjuncts.",
    ),
    CitationSpec(
        kg_node_id="argument_the_practical_syllogism_1d2e7506",
        passage_id="2ae32536-1de3-44a8-882b-6d6d5d1479b0",
        citation_type="primary_source",
        confidence=0.90,
        notes="EN VII.3 contains Aristotle's canonical discussion of practical reasoning in action.",
    ),
    CitationSpec(
        kg_node_id="argument_the_practical_syllogism_1d2e7506",
        passage_id="1a30d26e-2412-4bd7-8f9a-94f5684cbff0",
        citation_type="primary_source",
        confidence=0.95,
        notes="De Anima III.10 says intellect oriented to action and desire are what move an animal.",
    ),
    CitationSpec(
        kg_node_id="argument_two_way_powers_aristotle_i9j0k1l2",
        passage_id="cf9a2603-1217-4b9d-883e-c43223253eaa",
        citation_type="primary_source",
        confidence=0.98,
        notes="Metaphysics IX.2 distinguishes rational powers of opposites from non-rational powers ordered to one effect.",
    ),
    CitationSpec(
        kg_node_id="argument_two_way_powers_aristotle_i9j0k1l2",
        passage_id="6ba1f5f2-650f-4f62-a43e-937f6bcd03d6",
        citation_type="primary_source",
        confidence=0.98,
        notes="Metaphysics IX.5 adds that desire or choice determines which opposite a rational power will actualize.",
    ),
]

WEB_SOURCES = {
    "frankfurt_article": "https://www.pdcnet.org/jphil/content/jphil_1969_0066_0023_0829_0839%26gt",
    "frankfurt_mit_ocw": "https://ocw.mit.edu/courses/24-231-ethics-fall-2009/resources/mit24_231f09_lec25/",
    "bayle_dictionary_artfl": "https://artfl-project.uchicago.edu/dictionnaire-de-bayle",
    "bayle_rorarius_secondary": "https://periodicos.unb.br/index.php/fmc/article/view/12564",
    "leibniz_theodicy_britannica": "https://www.britannica.com/topic/Theodicy",
    "leibniz_theodicy_gutenberg": "https://www.gutenberg.org/files/17147/17147-h/17147-h.htm",
    "plato_laws_topostext": "https://topostext.org/work/484",
}


PLANNED_WORK_NODE_IDS = {work.node_id for work in NEW_WORKS}


async def ensure_node_exists(
    conn: asyncpg.Connection,
    node_id: str,
    *,
    allow_planned: bool = False,
) -> None:
    if allow_planned and node_id in PLANNED_WORK_NODE_IDS:
        return
    exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node_id,
    )
    if not exists:
        raise RuntimeError(f"Required node missing: {node_id}")


async def upsert_work_node(conn: asyncpg.Connection, work: WorkNode, apply: bool) -> bool:
    existing = await conn.fetchrow(
        f"SELECT node_id FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        work.node_id,
    )
    if existing:
        if apply:
            await conn.execute(
                f"""
                UPDATE {SCHEMA}.kg_nodes
                SET label = $2,
                    type = 'work',
                    period = $3,
                    description = $4,
                    alternative_names = '[]'::jsonb,
                    metadata = $5::jsonb,
                    updated_at = NOW()
                WHERE node_id = $1
                """,
                work.node_id,
                work.label,
                work.period,
                work.description,
                jd(work.metadata),
            )
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.kg_nodes (
                node_id, label, type, period, description, alternative_names, metadata, created_at, updated_at
            )
            VALUES ($1, $2, 'work', $3, $4, '[]'::jsonb, $5::jsonb, NOW(), NOW())
            """,
            work.node_id,
            work.label,
            work.period,
            work.description,
            jd(work.metadata),
        )
    return True


async def update_node(conn: asyncpg.Connection, update: NodeUpdate, apply: bool) -> None:
    await ensure_node_exists(conn, update.node_id)
    alt_names = update.alternative_names
    if alt_names is None:
        alt_names = await conn.fetchval(
            f"SELECT alternative_names FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
            update.node_id,
        )
        if isinstance(alt_names, str):
            alt_names = json.loads(alt_names)
    if apply:
        await conn.execute(
            f"""
            UPDATE {SCHEMA}.kg_nodes
            SET label = $2,
                description = $3,
                alternative_names = $4::jsonb,
                metadata = $5::jsonb,
                updated_at = NOW()
            WHERE node_id = $1
            """,
            update.node_id,
            update.label,
            update.description,
            jd(alt_names or []),
            jd(update.metadata),
        )


async def edge_exists(conn: asyncpg.Connection, edge: EdgeSpec) -> bool:
    exists = await conn.fetchval(
        f"""
        SELECT 1
        FROM {SCHEMA}.kg_edges
        WHERE source_id = $1 AND target_id = $2 AND relation = $3
        """,
        edge.source_id,
        edge.target_id,
        edge.relation,
    )
    return bool(exists)


async def ensure_edge(conn: asyncpg.Connection, edge: EdgeSpec, apply: bool) -> bool:
    allow_planned = not apply
    await ensure_node_exists(conn, edge.source_id, allow_planned=allow_planned)
    await ensure_node_exists(conn, edge.target_id, allow_planned=allow_planned)
    if await edge_exists(conn, edge):
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.kg_edges (edge_id, source_id, target_id, relation, metadata, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
            """,
            uuid.uuid4(),
            edge.source_id,
            edge.target_id,
            edge.relation,
            jd(edge.metadata),
        )
    return True


async def delete_edge(conn: asyncpg.Connection, edge: EdgeSpec, apply: bool) -> bool:
    exists = await edge_exists(conn, edge)
    if not exists:
        return False
    if apply:
        await conn.execute(
            f"""
            DELETE FROM {SCHEMA}.kg_edges
            WHERE source_id = $1 AND target_id = $2 AND relation = $3
            """,
            edge.source_id,
            edge.target_id,
            edge.relation,
        )
    return True


async def ensure_citation(conn: asyncpg.Connection, citation: CitationSpec, apply: bool) -> bool:
    await ensure_node_exists(conn, citation.kg_node_id)
    passage_exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.passages WHERE passage_id = $1",
        citation.passage_id,
    )
    if not passage_exists:
        raise RuntimeError(f"Required passage missing: {citation.passage_id}")
    exists = await conn.fetchval(
        f"""
        SELECT 1
        FROM {SCHEMA}.passage_citations
        WHERE passage_id = $1 AND kg_node_id = $2
        """,
        citation.passage_id,
        citation.kg_node_id,
    )
    if exists:
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.passage_citations (
                citation_id, passage_id, kg_node_id, citation_type, confidence, notes, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """,
            uuid.uuid4(),
            citation.passage_id,
            citation.kg_node_id,
            citation.citation_type,
            citation.confidence,
            citation.notes,
        )
    return True


async def main(confirm: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(dsn=database_url, statement_cache_size=0)
    try:
        created_works = 0
        updated_nodes = 0
        inserted_edges = 0
        deleted_edges = 0
        inserted_citations = 0

        for update in NODE_UPDATES:
            await update_node(conn, update, confirm)
            updated_nodes += 1

        for work in NEW_WORKS:
            if await upsert_work_node(conn, work, confirm):
                created_works += 1

        for edge in EDGES_TO_ENSURE:
            if await ensure_edge(conn, edge, confirm):
                inserted_edges += 1

        for edge in EDGES_TO_DELETE:
            if await delete_edge(conn, edge, confirm):
                deleted_edges += 1

        for citation in CITATIONS_TO_ENSURE:
            if await ensure_citation(conn, citation, confirm):
                inserted_citations += 1

        summary = {
            "run_tag": RUN_TAG,
            "applied": confirm,
            "counts": {
                "updated_nodes": updated_nodes,
                "created_work_nodes": created_works,
                "inserted_edges": inserted_edges,
                "deleted_edges": deleted_edges,
                "inserted_passage_citations": inserted_citations,
            },
            "batch_nodes": [update.node_id for update in NODE_UPDATES],
            "new_work_nodes": [work.node_id for work in NEW_WORKS],
            "web_sources": WEB_SOURCES,
            "decisions": [
                {
                    "node_id": "argument_aristotles_potentialityactuality_argument_20c5ac91",
                    "status": "retained_and_sourced",
                    "sources": ["Aristotle, Metaphysics IX.3-4"],
                },
                {
                    "node_id": "argument_aristotle_event_taxonomy",
                    "status": "retained_retitled_and_sourced",
                    "sources": [
                        "Alexander of Aphrodisias, De Fato 4-5",
                        "Aristotle, Physics II.4-6",
                    ],
                    "notes": ["flagged as editorial label"],
                },
                {
                    "node_id": "argument_aristotles_voluntary_action_argument_eph_hemin_e5dd9188",
                    "status": "retained_and_sourced",
                    "sources": ["Aristotle, Nicomachean Ethics III.1; III.5"],
                },
                {
                    "node_id": "argument_platos_laws_x_selfmotion_argument_8c31a166",
                    "status": "retained_and_work_sourced",
                    "sources": ["Plato, Laws X 891e-899d"],
                },
                {
                    "node_id": "argument_sea_battle_aristotle_f6g7h8i9",
                    "status": "retained_and_sourced",
                    "sources": ["Aristotle, De Interpretatione 9.2; 9.15"],
                    "notes": ["flagged as standard later label"],
                },
                {
                    "node_id": "argument_the_practical_syllogism_1d2e7506",
                    "status": "retained_and_sourced",
                    "sources": ["Aristotle, De Anima III.10", "Aristotle, Nicomachean Ethics VII.3"],
                    "notes": ["flagged as standard modern label"],
                },
                {
                    "node_id": "argument_two_way_powers_aristotle_i9j0k1l2",
                    "status": "retained_and_sourced",
                    "sources": ["Aristotle, Metaphysics IX.2; IX.5"],
                    "notes": ["flagged as standard later label"],
                },
                {
                    "node_id": "argument_frankfurt_cases_1o2p3q4r",
                    "status": "retained_and_work_sourced",
                    "sources": [
                        "Harry G. Frankfurt, Alternate Possibilities and Moral Responsibility (1969)"
                    ],
                    "notes": ["flagged as standard later label for Frankfurt's cases"],
                },
                {
                    "node_id": "argument_argument_from_animal_rationality_4629e983",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": [
                        'Pierre Bayle, Dictionnaire historique et critique, article "Rorarius"'
                    ],
                },
                {
                    "node_id": "argument_best_of_all_possible_worlds_cb9e1741",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": [
                        "G. W. Leibniz, Essais de Théodicée sur la bonté de Dieu, la liberté de l'homme et l'origine du mal (1710)"
                    ],
                },
            ],
        }

        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(jd(summary) + "\n", encoding="utf-8")

        lines = [
            "# KG Manual Review Batch 01 Results",
            "",
            f"- Applied: `{confirm}`",
            f"- Updated nodes: `{updated_nodes}`",
            f"- Created work nodes: `{created_works}`",
            f"- Inserted edges: `{inserted_edges}`",
            f"- Deleted edges: `{deleted_edges}`",
            f"- Inserted passage citations: `{inserted_citations}`",
            "",
            "## Decisions",
            "",
        ]
        for decision in summary["decisions"]:
            lines.append(f"- `{decision['node_id']}`: `{decision['status']}`")
            lines.append(f"  Sources: {', '.join(decision['sources'])}")
            if decision.get("notes"):
                lines.append(f"  Notes: {', '.join(decision['notes'])}")
        lines.extend(
            [
                "",
                "## Web Verification Sources",
                "",
                f"- Frankfurt article: {WEB_SOURCES['frankfurt_article']}",
                f"- MIT OCW reference page: {WEB_SOURCES['frankfurt_mit_ocw']}",
                f"- Bayle dictionary: {WEB_SOURCES['bayle_dictionary_artfl']}",
                f"- Bayle Rorarius secondary verification: {WEB_SOURCES['bayle_rorarius_secondary']}",
                f"- Leibniz Theodicy: {WEB_SOURCES['leibniz_theodicy_britannica']}",
                f"- Leibniz public-domain text: {WEB_SOURCES['leibniz_theodicy_gutenberg']}",
                f"- Plato Laws X reference text: {WEB_SOURCES['plato_laws_topostext']}",
                "",
            ]
        )
        REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not confirm:
            print("\nDry run only. Re-run with --confirm to apply changes.")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true", help="Apply the reviewed fixes")
    args = parser.parse_args()
    asyncio.run(main(confirm=args.confirm))
