#!/usr/bin/env python3
"""
Apply the second reviewed manual KG provenance fixes without generating content.

This script only:
- updates reviewed node labels/descriptions/metadata
- enriches existing source work metadata when exact bibliography is verified
- creates verified source work/publication nodes when needed
- adds reviewed `source_for` / `contains` / `authored_by` edges
- removes clearly unsupported reviewed edges
- adds passage citations tied to existing passages in the corpus

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/apply_manual_review_batch_02.py
    uv run --directory database python database/scripts/apply_manual_review_batch_02.py --confirm
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
RUN_TAG = "kg_manual_review_batch_02_2026_03_08"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-08-kg-manual-review-batch-02-results.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-08-kg-manual-review-batch-02-results.md"


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
class MetadataPatch:
    node_id: str
    patch: dict[str, Any]


@dataclass(frozen=True)
class SourceNode:
    node_id: str
    label: str
    node_type: str
    period: str
    description: str
    metadata: dict[str, Any]
    author_person_ids: list[str]


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
        node_id="concept_tripartite_soul_plato_e5f6g7h8",
        label="Tripartite Soul (Τριμερής Ψυχή)",
        description=(
            "Standard scholarly label for Plato's division of the soul in Republic IV. "
            "Plato distinguishes rational, spirited, and appetitive elements and uses "
            "psychic conflict to argue that the soul is not simple in the relevant respect."
        ),
        metadata={
            "formulator": "Plato",
            "greek_term": "τριμερής ψυχή (trimeres psyche)",
            "latin_term": "anima tripartita",
            "source_work": "Republic IV",
            "primary_source": "Plato, Republic IV 436a-441c",
            "ancient_sources": ["Plato, Republic IV 436a-441c"],
            "scholarly_status": (
                "standard scholarly label for Plato's partition of the soul in Republic IV"
            ),
        },
    ),
    NodeUpdate(
        node_id="quote_aristotle_origin_principle_9cb3c262",
        label="ὧν δʼ ἐν αὐτῷ ἡ ἀρχή, ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή.",
        description="Verbatim Greek quotation from Aristotle, Nicomachean Ethics III.1.",
        metadata={
            "source_work": "Nicomachean Ethics III.1",
            "primary_source": "Aristotle, Nicomachean Ethics III.1",
            "ancient_sources": ["Aristotle, Nicomachean Ethics III.1"],
            "summary": "Verbatim Greek quotation from Nicomachean Ethics III.1.",
            "related_concepts": [
                "To Eph' Hêmin (Τὸ ἐφ' ἡμῖν) - What is In Our Power"
            ],
            "quote_status": "verbatim Greek quotation",
            "quote_text_original": "ὧν δʼ ἐν αὐτῷ ἡ ἀρχή, ἐπʼ αὐτῷ καὶ τὸ πράττειν καὶ μή.",
            "quote_language": "grc",
            "source_cts_urn": "urn:cts:greekLit:tlg0086.tlg010.perseus-grc2:3.1",
            "verification_url": "https://el.wikisource.org/wiki/%CE%97%CE%B8%CE%B9%CE%BA%CE%AC_%CE%9D%CE%B9%CE%BA%CE%BF%CE%BC%CE%AC%CF%87%CE%B5%CE%B9%CE%B1/%CE%93",
        },
    ),
    NodeUpdate(
        node_id="concept_illusionism_free_will_6d7e8f9g",
        label="Free Will Illusionism",
        description=(
            "Contemporary position associated with Saul Smilansky's Free Will and Illusion "
            "(2000). Smilansky argues that ordinary beliefs in libertarian free will and basic "
            "desert responsibility are illusory, while also arguing that such beliefs play an "
            "important practical role in ordinary moral life."
        ),
        metadata={
            "formulator": "Saul Smilansky",
            "source_work": "Free Will and Illusion",
            "primary_source": "Saul Smilansky, Free Will and Illusion (2000)",
            "scholarly_status": "contemporary position label",
        },
    ),
    NodeUpdate(
        node_id="concept_knobe_effect_2z3a4b5c",
        label="Knobe Effect",
        description=(
            "Standard label for the asymmetry reported in Joshua Knobe's 2003 article "
            "'Intentional action and side effects in ordinary language': in otherwise parallel "
            "cases, subjects are more likely to judge a bad side effect intentional than a good one."
        ),
        metadata={
            "formulator": "Joshua Knobe",
            "source_work": "Intentional action and side effects in ordinary language",
            "primary_source": (
                "Joshua Knobe, 'Intentional action and side effects in ordinary language' (2003)"
            ),
            "scholarly_status": "standard label for an empirical asymmetry first reported in 2003",
        },
    ),
    NodeUpdate(
        node_id="concept_manipulation_argument",
        label="Manipulation Argument",
        description=(
            "Contemporary incompatibilist argument, prominently developed by Derk Pereboom, "
            "that compares ordinary agency with manipulated or engineered cases in order to "
            "challenge whether such agents have the kind of free will required for basic desert "
            "moral responsibility."
        ),
        metadata={
            "formulator": "Derk Pereboom",
            "source_work": "Living without Free Will",
            "primary_source": "Derk Pereboom, Living without Free Will (2001)",
            "scholarly_status": (
                "contemporary argument label; here anchored in Pereboom's four-case formulation"
            ),
        },
    ),
    NodeUpdate(
        node_id="concept_principle_alternative_possibilities_5s6t7u8v",
        label="Principle of Alternative Possibilities (PAP)",
        description=(
            "Standard discussion label for the principle that a person is morally responsible "
            "for what they have done only if they could have done otherwise. Frankfurt's 1969 "
            "article formulates the principle explicitly in order to challenge it."
        ),
        metadata={
            "source_work": "Alternate Possibilities and Moral Responsibility",
            "primary_source": (
                "Harry G. Frankfurt, 'Alternate Possibilities and Moral Responsibility' (1969)"
            ),
            "scholarly_status": "standard discussion label in contemporary responsibility debates",
        },
    ),
    NodeUpdate(
        node_id="concept_public_health_model_7e8f9g0h",
        label="Public Health-Quarantine Model of Criminal Justice",
        description=(
            "Contemporary free-will-skeptical model of criminal justice developed by Gregg D. "
            "Caruso. The model rejects basic-desert retribution and instead treats prevention, "
            "incapacitation, and rehabilitation on a public-health or quarantine analogy."
        ),
        metadata={
            "formulator": "Gregg D. Caruso",
            "source_work": "Free Will Skepticism and Criminal Behavior",
            "primary_source": (
                "Gregg D. Caruso, 'Free Will Skepticism and Criminal Behavior' (2016)"
            ),
            "scholarly_status": "contemporary policy model in the free will skepticism literature",
        },
    ),
    NodeUpdate(
        node_id="concept_semicompatibilism_6t7u8v9w",
        label="Semicompatibilism",
        description=(
            "John Martin Fischer's view that moral responsibility is compatible with determinism "
            "even if free will, understood in terms of alternative possibilities, is not. In "
            "Responsibility and Control, Fischer and Ravizza defend this position through an "
            "account of guidance control and reasons-responsiveness."
        ),
        metadata={
            "formulator": "John Martin Fischer",
            "source_work": "Responsibility and Control",
            "primary_source": "John Martin Fischer and Mark Ravizza, Responsibility and Control (1998)",
            "scholarly_status": "contemporary position label",
        },
    ),
    NodeUpdate(
        node_id="debate_middle_platonist_fate_interpretation",
        label="Interpretation of Middle Platonist Fate Theory",
        description=(
            "Contemporary scholarly debate over whether Middle Platonists restricted the scope "
            "of fate to preserve voluntary action, or instead accepted universal causal order "
            "while distinguishing fate, providence, and what depends on us in a different way."
        ),
        metadata={
            "positions": {
                "revisionist": {
                    "works": ["pub_boysstones_2007_middle_platonists"],
                    "scholars": ["George Boys-Stones"],
                },
                "conventional": {
                    "works": [
                        "pub_dillon_1977_middle_platonists",
                        "pub_amand_1945_fatalisme",
                    ],
                    "scholars": ["John Dillon", "David Amand"],
                },
            },
            "debate_type": "scholarly interpretation",
            "central_question": "Did Middle Platonists restrict fate in order to preserve human autonomy?",
            "resolution_status": "ongoing",
            "scholarly_status": "contemporary interpretive debate",
        },
    ),
    NodeUpdate(
        node_id="argument_cambridge_platonist_defense_of_plastic_nature_d49aa761",
        label="Cudworth's Plastic Nature Argument",
        description=(
            "In The True Intellectual System of the Universe, Ralph Cudworth introduces "
            "'plastic nature' as a non-conscious, instrumentally ordered principle through "
            "which natural processes are governed. The doctrine is presented to explain natural "
            "order without treating blind matter as sufficient or making God the immediate "
            "efficient cause of every event."
        ),
        metadata={
            "formulator": "Ralph Cudworth",
            "argument_type": "metaphysical / philosophical theology",
            "source_work": "The True Intellectual System of the Universe",
            "primary_source": (
                "Ralph Cudworth, The True Intellectual System of the Universe (1678), Book I, ch. 3"
            ),
            "scholarly_status": (
                "node narrowed from a broader Cambridge Platonist framing to Cudworth's explicit formulation"
            ),
        },
    ),
]

METADATA_PATCHES = [
    MetadataPatch(
        node_id="work_living_without_free_will_pereboom_0h1i2j3k",
        patch={
            "date": "2001",
            "year": 2001,
            "author": "Derk Pereboom",
            "publisher": "Cambridge University Press",
            "doi": "10.1017/cbo9780511498824",
            "reference_url": "https://doi.org/10.1017/cbo9780511498824",
            "verified_by": RUN_TAG,
        },
    ),
    MetadataPatch(
        node_id="work_responsibility_and_control_fischer_ravizza_2j3k4l5m",
        patch={
            "date": "1998",
            "year": 1998,
            "author": "John Martin Fischer and Mark Ravizza",
            "publisher": "Cambridge University Press",
            "doi": "10.1017/cbo9780511814594",
            "reference_url": "https://doi.org/10.1017/cbo9780511814594",
            "verified_by": RUN_TAG,
        },
    ),
]

NEW_SOURCE_NODES = [
    SourceNode(
        node_id="work_smilansky_free_will_illusion_2000",
        label="Free Will and Illusion",
        node_type="work",
        period="Contemporary",
        description="Saul Smilansky, Free Will and Illusion (Oxford University Press, 2000).",
        metadata={
            "type": "book",
            "year": 2000,
            "author": "Saul Smilansky",
            "publisher": "Oxford University Press",
            "doi": "10.1093/oso/9780198250180.001.0001",
            "reference_url": "https://doi.org/10.1093/oso/9780198250180.001.0001",
            "verified_by": RUN_TAG,
        },
        author_person_ids=["person_smilansky_saul_9c0d1e2f"],
    ),
    SourceNode(
        node_id="pub_knobe_2003_intentional_action_side_effects",
        label="Intentional action and side effects in ordinary language",
        node_type="publication",
        period="Contemporary",
        description=(
            "Joshua Knobe, 'Intentional action and side effects in ordinary language,' "
            "Analysis 63.3 (2003): 190-194."
        ),
        metadata={
            "type": "journal article",
            "year": 2003,
            "author": "Joshua Knobe",
            "journal": "Analysis",
            "volume": 63,
            "issue": 3,
            "pages": "190-194",
            "doi": "10.1093/analys/63.3.190",
            "reference_url": "https://doi.org/10.1093/analys/63.3.190",
            "verified_by": RUN_TAG,
        },
        author_person_ids=["person_knobe_joshua_5i6j7k8l"],
    ),
    SourceNode(
        node_id="pub_caruso_2016_free_will_skepticism_criminal_behavior",
        label="Free Will Skepticism and Criminal Behavior",
        node_type="publication",
        period="Contemporary",
        description=(
            "Gregg D. Caruso, 'Free Will Skepticism and Criminal Behavior,' Southwest "
            "Philosophy Review 32.1 (2016): 25-48."
        ),
        metadata={
            "type": "journal article",
            "year": 2016,
            "author": "Gregg D. Caruso",
            "journal": "Southwest Philosophy Review",
            "volume": 32,
            "issue": 1,
            "pages": "25-48",
            "doi": "10.5840/swphilreview20163214",
            "reference_url": "https://doi.org/10.5840/swphilreview20163214",
            "verified_by": RUN_TAG,
        },
        author_person_ids=["person_caruso_gregg_0d1e2f3g"],
    ),
    SourceNode(
        node_id="work_cudworth_true_intellectual_system_1678",
        label="The True Intellectual System of the Universe",
        node_type="work",
        period="Early Modern",
        description=(
            "Ralph Cudworth, The True Intellectual System of the Universe (first part, 1678). "
            "Reference link is an Internet Archive scan of a later edition."
        ),
        metadata={
            "type": "book",
            "year": 1678,
            "author": "Ralph Cudworth",
            "short_title": "True Intellectual System",
            "reference_url": "https://archive.org/details/in.ernet.dli.2015.152609",
            "reference_note": "Internet Archive scan of a later edition",
            "verified_by": RUN_TAG,
        },
        author_person_ids=["person_ralph_cudworth_77de5c65"],
    ),
]

EDGES_TO_ENSURE = [
    EdgeSpec(
        source_id="work_republic_plato_c380bce_c3d4e5f6",
        target_id="concept_tripartite_soul_plato_e5f6g7h8",
        relation="source_for",
        metadata={"reference": "IV 436a-441c", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_living_without_free_will_pereboom_0h1i2j3k",
        target_id="concept_manipulation_argument",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_living_without_free_will_pereboom_0h1i2j3k",
        target_id="concept_manipulation_argument",
        relation="source_for",
        metadata={"reference": "four-case manipulation argument", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_responsibility_and_control_fischer_ravizza_2j3k4l5m",
        target_id="concept_semicompatibilism_6t7u8v9w",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_responsibility_and_control_fischer_ravizza_2j3k4l5m",
        target_id="concept_semicompatibilism_6t7u8v9w",
        relation="source_for",
        metadata={"reference": "guidance control account", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_frankfurt_alternate_possibilities_1969",
        target_id="concept_principle_alternative_possibilities_5s6t7u8v",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_frankfurt_alternate_possibilities_1969",
        target_id="concept_principle_alternative_possibilities_5s6t7u8v",
        relation="source_for",
        metadata={"reference": "opening formulation of PAP", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="pub_dillon_1977_middle_platonists",
        target_id="debate_middle_platonist_fate_interpretation",
        relation="source_for",
        metadata={"reference": "conventional reading", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="pub_amand_1945_fatalisme",
        target_id="debate_middle_platonist_fate_interpretation",
        relation="source_for",
        metadata={"reference": "conventional reading", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="pub_boysstones_2007_middle_platonists",
        target_id="debate_middle_platonist_fate_interpretation",
        relation="source_for",
        metadata={"reference": "revisionist reading", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_smilansky_free_will_illusion_2000",
        target_id="concept_illusionism_free_will_6d7e8f9g",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_smilansky_free_will_illusion_2000",
        target_id="concept_illusionism_free_will_6d7e8f9g",
        relation="source_for",
        metadata={"reference": "book-level statement of illusionism", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="pub_knobe_2003_intentional_action_side_effects",
        target_id="concept_knobe_effect_2z3a4b5c",
        relation="source_for",
        metadata={"reference": "side-effect asymmetry", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="pub_caruso_2016_free_will_skepticism_criminal_behavior",
        target_id="concept_public_health_model_7e8f9g0h",
        relation="source_for",
        metadata={"reference": "public health-quarantine model", "reviewed_by": RUN_TAG},
    ),
    EdgeSpec(
        source_id="work_cudworth_true_intellectual_system_1678",
        target_id="argument_cambridge_platonist_defense_of_plastic_nature_d49aa761",
        relation="contains",
        metadata={},
    ),
    EdgeSpec(
        source_id="work_cudworth_true_intellectual_system_1678",
        target_id="argument_cambridge_platonist_defense_of_plastic_nature_d49aa761",
        relation="source_for",
        metadata={"reference": "Book I, ch. 3", "reviewed_by": RUN_TAG},
    ),
]

for source_node in NEW_SOURCE_NODES:
    for author_person_id in source_node.author_person_ids:
        EDGES_TO_ENSURE.append(
            EdgeSpec(
                source_id=source_node.node_id,
                target_id=author_person_id,
                relation="authored_by",
                metadata={"reviewed_by": RUN_TAG},
            )
        )

EDGES_TO_DELETE = [
    EdgeSpec(
        source_id="concept_illusionism_free_will_6d7e8f9g",
        target_id="concept_public_health_model_7e8f9g0h",
        relation="critiques",
        metadata={},
    ),
    EdgeSpec(
        source_id="concept_knobe_effect_2z3a4b5c",
        target_id="concept_reactive_attitudes_7u8v9w0x",
        relation="supports",
        metadata={},
    ),
    EdgeSpec(
        source_id="argument_cambridge_platonist_defense_of_plastic_nature_d49aa761",
        target_id="concept_agent_causation_0l4g5h13",
        relation="supports",
        metadata={},
    ),
]

CITATIONS_TO_ENSURE = [
    CitationSpec(
        kg_node_id="quote_aristotle_origin_principle_9cb3c262",
        passage_id="61f93a32-769e-498b-968d-de545a9bd124",
        citation_type="primary_source",
        confidence=0.99,
        notes="Verbatim Greek quotation from Nicomachean Ethics III.1.",
    ),
]

WEB_SOURCES = {
    "smilansky_free_will_and_illusion": "https://doi.org/10.1093/oso/9780198250180.001.0001",
    "knobe_2003_analysis": "https://doi.org/10.1093/analys/63.3.190",
    "pereboom_living_without_free_will": "https://doi.org/10.1017/cbo9780511498824",
    "fischer_ravizza_responsibility_and_control": "https://doi.org/10.1017/cbo9780511814594",
    "caruso_2016_criminal_behavior": "https://doi.org/10.5840/swphilreview20163214",
    "cudworth_archive_scan": "https://archive.org/details/in.ernet.dli.2015.152609",
    "frankfurt_1969_article": "https://www.pdcnet.org/jphil/content/jphil_1969_0066_0023_0829_0839%26gt",
}

PLANNED_SOURCE_NODE_IDS = {node.node_id for node in NEW_SOURCE_NODES}


async def ensure_node_exists(
    conn: asyncpg.Connection,
    node_id: str,
    *,
    allow_planned: bool = False,
) -> None:
    if allow_planned and node_id in PLANNED_SOURCE_NODE_IDS:
        return
    exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node_id,
    )
    if not exists:
        raise RuntimeError(f"Required node missing: {node_id}")


async def upsert_source_node(
    conn: asyncpg.Connection,
    node: SourceNode,
    apply: bool,
) -> bool:
    existing = await conn.fetchrow(
        f"SELECT node_id FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node.node_id,
    )
    if existing:
        if apply:
            await conn.execute(
                f"""
                UPDATE {SCHEMA}.kg_nodes
                SET label = $2,
                    type = $3,
                    period = $4,
                    description = $5,
                    alternative_names = '[]'::jsonb,
                    metadata = $6::jsonb,
                    updated_at = NOW()
                WHERE node_id = $1
                """,
                node.node_id,
                node.label,
                node.node_type,
                node.period,
                node.description,
                jd(node.metadata),
            )
        return False
    if apply:
        await conn.execute(
            f"""
            INSERT INTO {SCHEMA}.kg_nodes (
                node_id, label, type, period, description, alternative_names, metadata, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, '[]'::jsonb, $6::jsonb, NOW(), NOW())
            """,
            node.node_id,
            node.label,
            node.node_type,
            node.period,
            node.description,
            jd(node.metadata),
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


async def patch_metadata(conn: asyncpg.Connection, patch: MetadataPatch, apply: bool) -> None:
    await ensure_node_exists(conn, patch.node_id)
    current = await conn.fetchval(
        f"SELECT metadata FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        patch.node_id,
    )
    if isinstance(current, str):
        current = json.loads(current)
    merged = dict(current or {})
    merged.update(patch.patch)
    if apply:
        await conn.execute(
            f"""
            UPDATE {SCHEMA}.kg_nodes
            SET metadata = $2::jsonb,
                updated_at = NOW()
            WHERE node_id = $1
            """,
            patch.node_id,
            jd(merged),
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
        updated_nodes = 0
        patched_metadata_nodes = 0
        created_source_nodes = 0
        inserted_edges = 0
        deleted_edges = 0
        inserted_citations = 0

        for update in NODE_UPDATES:
            await update_node(conn, update, confirm)
            updated_nodes += 1

        for patch in METADATA_PATCHES:
            await patch_metadata(conn, patch, confirm)
            patched_metadata_nodes += 1

        for node in NEW_SOURCE_NODES:
            if await upsert_source_node(conn, node, confirm):
                created_source_nodes += 1

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
                "patched_source_metadata_nodes": patched_metadata_nodes,
                "created_source_nodes": created_source_nodes,
                "inserted_edges": inserted_edges,
                "deleted_edges": deleted_edges,
                "inserted_passage_citations": inserted_citations,
            },
            "batch_nodes": [update.node_id for update in NODE_UPDATES],
            "new_source_nodes": [node.node_id for node in NEW_SOURCE_NODES],
            "web_sources": WEB_SOURCES,
            "decisions": [
                {
                    "node_id": "concept_tripartite_soul_plato_e5f6g7h8",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Plato, Republic IV 436a-441c"],
                    "notes": ["work-level source only; Republic passages are not currently loaded in the local passage table"],
                },
                {
                    "node_id": "quote_aristotle_origin_principle_9cb3c262",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Aristotle, Nicomachean Ethics III.1"],
                    "notes": ["corrected to a single verbatim Greek quotation"],
                },
                {
                    "node_id": "concept_illusionism_free_will_6d7e8f9g",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Saul Smilansky, Free Will and Illusion (2000)"],
                    "notes": ["flagged as contemporary position label"],
                },
                {
                    "node_id": "concept_knobe_effect_2z3a4b5c",
                    "status": "retained_rewritten_and_publication_sourced",
                    "sources": [
                        "Joshua Knobe, 'Intentional action and side effects in ordinary language' (2003)"
                    ],
                    "notes": ["flagged as standard label for an empirical asymmetry"],
                },
                {
                    "node_id": "concept_manipulation_argument",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Derk Pereboom, Living without Free Will (2001)"],
                    "notes": ["flagged as contemporary argument label"],
                },
                {
                    "node_id": "concept_principle_alternative_possibilities_5s6t7u8v",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": [
                        "Harry G. Frankfurt, 'Alternate Possibilities and Moral Responsibility' (1969)"
                    ],
                    "notes": ["flagged as standard discussion label"],
                },
                {
                    "node_id": "concept_public_health_model_7e8f9g0h",
                    "status": "retained_rewritten_and_publication_sourced",
                    "sources": [
                        "Gregg D. Caruso, 'Free Will Skepticism and Criminal Behavior' (2016)"
                    ],
                    "notes": ["flagged as contemporary policy model"],
                },
                {
                    "node_id": "concept_semicompatibilism_6t7u8v9w",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["John Martin Fischer and Mark Ravizza, Responsibility and Control (1998)"],
                    "notes": ["flagged as contemporary position label"],
                },
                {
                    "node_id": "debate_middle_platonist_fate_interpretation",
                    "status": "retained_rewritten_and_publication_sourced",
                    "sources": [
                        "John Dillon, The Middle Platonists (1977)",
                        "David Amand, Fatalisme et liberté dans l'antiquité grecque (1945)",
                        "George Boys-Stones, 'Middle Platonists on Fate and Human Autonomy' (2007)",
                    ],
                    "notes": ["flagged as contemporary interpretive debate"],
                },
                {
                    "node_id": "argument_cambridge_platonist_defense_of_plastic_nature_d49aa761",
                    "status": "retained_retitled_rewritten_and_work_sourced",
                    "sources": [
                        "Ralph Cudworth, The True Intellectual System of the Universe (1678), Book I, ch. 3"
                    ],
                    "notes": ["narrowed from a broad Cambridge Platonist framing to Cudworth's explicit formulation"],
                },
            ],
        }

        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(jd(summary) + "\n", encoding="utf-8")

        lines = [
            "# KG Manual Review Batch 02 Results",
            "",
            f"- Applied: `{confirm}`",
            f"- Updated nodes: `{updated_nodes}`",
            f"- Patched source metadata nodes: `{patched_metadata_nodes}`",
            f"- Created source nodes: `{created_source_nodes}`",
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
                f"- Smilansky book DOI: {WEB_SOURCES['smilansky_free_will_and_illusion']}",
                f"- Knobe article DOI: {WEB_SOURCES['knobe_2003_analysis']}",
                f"- Pereboom book DOI: {WEB_SOURCES['pereboom_living_without_free_will']}",
                f"- Fischer/Ravizza book DOI: {WEB_SOURCES['fischer_ravizza_responsibility_and_control']}",
                f"- Caruso article DOI: {WEB_SOURCES['caruso_2016_criminal_behavior']}",
                f"- Cudworth archive scan: {WEB_SOURCES['cudworth_archive_scan']}",
                f"- Frankfurt article: {WEB_SOURCES['frankfurt_1969_article']}",
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
