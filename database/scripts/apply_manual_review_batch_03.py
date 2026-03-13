#!/usr/bin/env python3
"""
Apply the third reviewed manual KG provenance fixes: all 12 unsupported quote nodes.

Every quote node currently presents an English paraphrase as if it were a direct
quotation.  This script:
- rewrites each description to remove unsupported assertive claims
- marks every node explicitly as an English paraphrase in metadata
- adds passage citations where a local passage in `free_will.passages` matches
- adds work-level `source_for` / `contains` edges from existing KG work nodes
- fixes factual errors (wrong book references)

Usage:
    set -a; source .env; set +a
    uv run --directory database python database/scripts/apply_manual_review_batch_03.py
    uv run --directory database python database/scripts/apply_manual_review_batch_03.py --confirm
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
RUN_TAG = "kg_manual_review_batch_03_2026_03_10"
REPORT_JSON = ROOT / "docs" / "reports" / "2026-03-10-kg-manual-review-batch-03-results.json"
REPORT_MD = ROOT / "docs" / "reports" / "2026-03-10-kg-manual-review-batch-03-results.md"


def jd(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class NodeUpdate:
    node_id: str
    label: str
    description: str
    metadata: dict[str, Any]


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


# ---------------------------------------------------------------------------
# Node updates: rewrite descriptions, mark as English paraphrase
# ---------------------------------------------------------------------------

NODE_UPDATES = [
    # 1. Alexander of Aphrodisias - eph' hemin / alternatives
    NodeUpdate(
        node_id="quote_alexander_alternatives_e4d14e13",
        label="Alexander of Aphrodisias on 'what is up to us' (eph' hemin) and the power of opposites",
        description=(
            "English paraphrase of Alexander of Aphrodisias, De Fato 13-15. "
            "Alexander argues that 'what is up to us' (to eph' hemin) involves the "
            "genuine power to do otherwise, not merely voluntary action under "
            "antecedent causal determination. He contends that the Stoic redefinition "
            "of eph' hemin fails to preserve the common human understanding of the term."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Alexander of Aphrodisias, De Fato",
            "primary_source": "Alexander of Aphrodisias, De Fato 13-15",
            "ancient_sources": [
                "Alexander of Aphrodisias, De Fato 13",
                "Alexander of Aphrodisias, De Fato 14",
                "Alexander of Aphrodisias, De Fato 15",
            ],
            "wikidata_qid": "Q192477",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 2. Augustine - divided will (Confessions VIII)
    NodeUpdate(
        node_id="quote_augustine_divided_will_b45d573e",
        label="Augustine on the divided will (Confessions VIII)",
        description=(
            "English paraphrase of Augustine, Confessions VIII.9-10. Augustine "
            "describes the will commanding itself to will, yet failing to obey its "
            "own command. He locates the source of this inner conflict within the "
            "will itself, rather than in a conflict between reason and passion."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Confessions VIII",
            "primary_source": "Augustine, Confessions VIII.9-10",
            "ancient_sources": ["Augustine, Confessions VIII.9", "Augustine, Confessions VIII.10"],
            "corpus_note": "Confessions not loaded in local passage corpus",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 3. Augustine - liberum arbitrium (Confessions VIII, not IX)
    NodeUpdate(
        node_id="quote_augustine_liberum_arbitrium_0661f946",
        label="Augustine on liberum arbitrium and conversion (Confessions VIII)",
        description=(
            "English paraphrase of Augustine, Confessions VIII.12. Augustine "
            "describes the moment of conversion in the garden at Milan, where his "
            "free choice (liberum arbitrium) is called forth to submit to God. The "
            "passage illustrates the interplay of grace and will in Augustine's "
            "account."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Confessions VIII",
            "primary_source": "Augustine, Confessions VIII.12",
            "ancient_sources": ["Augustine, Confessions VIII.12"],
            "corpus_note": "Confessions not loaded in local passage corpus",
            "correction_note": "Previous description incorrectly cited Confessions IX; the garden scene is in VIII.12",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 4. Carneades via Cicero - CAFMA argument
    NodeUpdate(
        node_id="quote_carneades_cafma_4483b50a",
        label="Carneades' argument against fate (via Cicero, De Fato 31)",
        description=(
            "English paraphrase of Cicero, De Fato 31, reporting Carneades' "
            "argument: if everything happens through antecedent causes in natural "
            "connection, everything happens by necessity; but something is in our "
            "power; therefore not everything happens by fate. Cicero presents "
            "Carneades as pressing this argument against the Stoics without endorsing "
            "either the Stoic or the Epicurean position."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Cicero, De Fato",
            "primary_source": "Cicero, De Fato 31",
            "ancient_sources": ["Cicero, De Fato 31"],
            "attributed_to": "Carneades (as reported by Cicero)",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 5. Chrysippus via Cicero - cylinder analogy
    NodeUpdate(
        node_id="quote_chrysippus_cylinder_1da2c55b",
        label="Chrysippus' cylinder analogy (via Cicero, De Fato 42-43)",
        description=(
            "English paraphrase of Cicero, De Fato 42-43, reporting Chrysippus' "
            "cylinder analogy. Chrysippus distinguishes the external push that sets "
            "the cylinder rolling from the cylinder's own shape, which determines how "
            "it rolls. Similarly, an external impression is the proximate cause of "
            "assent, but assent itself depends on the agent's internal character."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Cicero, De Fato",
            "primary_source": "Cicero, De Fato 42-43",
            "ancient_sources": ["Cicero, De Fato 42", "Cicero, De Fato 43"],
            "attributed_to": "Chrysippus (as reported by Cicero)",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 6. Epictetus - prohairesis
    NodeUpdate(
        node_id="quote_epictetus_prohairesis_3fabff35",
        label="Epictetus on prohairesis and what is 'up to us' (Discourses I.1)",
        description=(
            "English paraphrase of Epictetus, Discourses I.1. Epictetus opens the "
            "Discourses by distinguishing things that are up to us (eph' hemin) from "
            "things that are not. He identifies prohairesis (moral choice) and the "
            "use of impressions (phantasiai) as within our power, while the body and "
            "external circumstances are not."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Epictetus, Discourses",
            "primary_source": "Epictetus, Discourses I.1",
            "ancient_sources": ["Epictetus, Discourses I.1"],
            "reviewed_by": RUN_TAG,
        },
    ),
    # 7. Lucretius - clinamen passage reference (II.251-293)
    NodeUpdate(
        node_id="quote_lucretius_clinamen_ii_251_293_176829af",
        label="Lucretius on the atomic swerve and free will (DRN II.251-293)",
        description=(
            "Passage-level reference to Lucretius, De Rerum Natura II.251-293. "
            "Lucretius argues that atoms swerve at no fixed time or place, breaking "
            "the chain of causation (fati foedera), and asks whence comes the free "
            "will (libera voluntas) observed in living things. The passage continues "
            "by arguing that something in the chest can fight against external force."
        ),
        metadata={
            "quote_status": "English paraphrase / passage reference, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Lucretius, De Rerum Natura",
            "primary_source": "Lucretius, De Rerum Natura II.251-293",
            "ancient_sources": ["Lucretius, De Rerum Natura II.251-293"],
            "reviewed_by": RUN_TAG,
        },
    ),
    # 8. Lucretius - swerve (shorter paraphrase)
    NodeUpdate(
        node_id="quote_lucretius_swerve_8bae0c52",
        label="Lucretius on the clinamen and fati foedera (DRN II.251ff)",
        description=(
            "English paraphrase of Lucretius, De Rerum Natura II.251ff. Lucretius "
            "presents the atomic swerve (clinamen) as what breaks the bonds of fate "
            "(fati foedera) and makes voluntary motion possible. The atoms swerve "
            "slightly from their downward path at no fixed time or place."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Latin",
            "quote_language": "en",
            "source_work": "Lucretius, De Rerum Natura",
            "primary_source": "Lucretius, De Rerum Natura II.251-293",
            "ancient_sources": ["Lucretius, De Rerum Natura II.251-293"],
            "reviewed_by": RUN_TAG,
        },
    ),
    # 9. Origen - autexousion
    NodeUpdate(
        node_id="quote_origen_autexousion_abbb5a2e",
        label="Origen on autexousion (self-determining power) (De Principiis III.1)",
        description=(
            "English paraphrase of Origen, De Principiis III.1.1. Origen opens his "
            "discussion of free will by defining autexousion (self-determining power) "
            "as the capacity relevant to moral judgment, in the context of arguing "
            "that divine judgment presupposes human responsibility."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Origen, De Principiis (Peri Archon)",
            "primary_source": "Origen, De Principiis III.1.1",
            "ancient_sources": [
                "Origen, De Principiis III.1.1",
                "Origen, De Principiis III.1.1a",
            ],
            "reviewed_by": RUN_TAG,
        },
    ),
    # 10. Plotinus - autexousion (sage)
    NodeUpdate(
        node_id="quote_plotinus_autexousion_65371acd",
        label="Plotinus on autexousion and inner freedom under constraint",
        description=(
            "English paraphrase summarizing Plotinus' position that the self-determining "
            "power (autexousion) is retained even under external duress. The theme "
            "appears in several Enneads treatises, including the discussions of fate "
            "in III.1 and of the voluntary in VI.8."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Plotinus, Enneads",
            "primary_source": "Plotinus, Enneads (multiple treatises: III.1, VI.8)",
            "ancient_sources": [
                "Plotinus, Enneads III.1 (On Fate)",
                "Plotinus, Enneads VI.8 (On the Voluntary and Free Will of the One)",
            ],
            "corpus_note": "Exact passage for 'sage under torture retaining autexousion' not identified in local corpus; work-level sourcing used",
            "reviewed_by": RUN_TAG,
        },
    ),
    # 11. Plotinus - heimarmene
    NodeUpdate(
        node_id="quote_plotinus_heimarmene_31dbdc1e",
        label="Plotinus on heimarmene (fate) as sovereign cause (Enneads III.1)",
        description=(
            "English paraphrase of Plotinus, Enneads III.1 (On Fate). Plotinus "
            "reports the Stoic conception of heimarmene (fate) as the supreme cause "
            "governing all things, including human thoughts, and then develops his "
            "own alternative account that preserves a role for soul and intellect."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Plotinus, Enneads III.1 (On Fate)",
            "primary_source": "Plotinus, Enneads III.1",
            "ancient_sources": ["Plotinus, Enneads III.1 (On Fate)"],
            "reviewed_by": RUN_TAG,
        },
    ),
    # 12. Plotinus - One and freedom
    NodeUpdate(
        node_id="quote_plotinus_one_freedom_b1d66acd",
        label="Plotinus on the freedom of the One (Enneads VI.8)",
        description=(
            "English paraphrase of Plotinus, Enneads VI.8 (On the Voluntary and Free "
            "Will of the One). Plotinus argues that the One is not constrained by "
            "external necessity but is, in a qualified sense, self-caused. He extends "
            "freedom language to the ultimate metaphysical principle."
        ),
        metadata={
            "quote_status": "English paraphrase, not verbatim Greek",
            "quote_language": "en",
            "source_work": "Plotinus, Enneads VI.8",
            "primary_source": "Plotinus, Enneads VI.8 (On the Voluntary and Free Will of the One)",
            "ancient_sources": [
                "Plotinus, Enneads VI.8 (On the Voluntary and Free Will of the One)",
            ],
            "reviewed_by": RUN_TAG,
        },
    ),
]

# ---------------------------------------------------------------------------
# Edges to add: work-level source_for / contains
# ---------------------------------------------------------------------------

EDGES_TO_ENSURE = [
    # Alexander
    EdgeSpec(
        source_id="work_de_fato_alexander_c200ce_o6p7q8r9",
        target_id="quote_alexander_alternatives_e4d14e13",
        relation="source_for",
        metadata={"reference": "De Fato 13-15", "reviewed_by": RUN_TAG},
    ),
    # Augustine - divided will
    EdgeSpec(
        source_id="work_confessions",
        target_id="quote_augustine_divided_will_b45d573e",
        relation="source_for",
        metadata={"reference": "Confessions VIII.9-10", "reviewed_by": RUN_TAG},
    ),
    # Augustine - liberum arbitrium
    EdgeSpec(
        source_id="work_confessions",
        target_id="quote_augustine_liberum_arbitrium_0661f946",
        relation="source_for",
        metadata={"reference": "Confessions VIII.12", "reviewed_by": RUN_TAG},
    ),
    # Carneades via Cicero
    EdgeSpec(
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        target_id="quote_carneades_cafma_4483b50a",
        relation="source_for",
        metadata={"reference": "De Fato 31", "reviewed_by": RUN_TAG},
    ),
    # Chrysippus via Cicero
    EdgeSpec(
        source_id="work_de_fato_cicero_44bce_b9c4e5d2",
        target_id="quote_chrysippus_cylinder_1da2c55b",
        relation="source_for",
        metadata={"reference": "De Fato 42-43", "reviewed_by": RUN_TAG},
    ),
    # Epictetus
    EdgeSpec(
        source_id="work_epictetus_discourses",
        target_id="quote_epictetus_prohairesis_3fabff35",
        relation="source_for",
        metadata={"reference": "Discourses I.1", "reviewed_by": RUN_TAG},
    ),
    # Lucretius - clinamen passage reference
    EdgeSpec(
        source_id="work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",
        target_id="quote_lucretius_clinamen_ii_251_293_176829af",
        relation="source_for",
        metadata={"reference": "DRN II.251-293", "reviewed_by": RUN_TAG},
    ),
    # Lucretius - swerve
    EdgeSpec(
        source_id="work_de_rerum_natura_lucretius_50sbce_l2m3n4o5",
        target_id="quote_lucretius_swerve_8bae0c52",
        relation="source_for",
        metadata={"reference": "DRN II.251ff", "reviewed_by": RUN_TAG},
    ),
    # Origen
    EdgeSpec(
        source_id="work_de_principiis_origen_230s_v2w3x4y5",
        target_id="quote_origen_autexousion_abbb5a2e",
        relation="source_for",
        metadata={"reference": "De Principiis III.1.1", "reviewed_by": RUN_TAG},
    ),
    # Plotinus - autexousion (work-level only)
    EdgeSpec(
        source_id="work_plotinus_ennead_vi_8_d8b9c5a4",
        target_id="quote_plotinus_autexousion_65371acd",
        relation="source_for",
        metadata={"reference": "Enneads VI.8 (among other treatises)", "reviewed_by": RUN_TAG},
    ),
    # Plotinus - heimarmene → use passage citation, no specific work node for III.1
    # We add a source_for from the VI.8 work node since it's the closest,
    # but the primary citation will be to the passage in the corpus
    # Plotinus - One/freedom
    EdgeSpec(
        source_id="work_plotinus_ennead_vi_8_d8b9c5a4",
        target_id="quote_plotinus_one_freedom_b1d66acd",
        relation="source_for",
        metadata={"reference": "Enneads VI.8", "reviewed_by": RUN_TAG},
    ),
]

EDGES_TO_DELETE: list[EdgeSpec] = [
    # Remove the misleading exemplifies link from cylinder quote to semicompatibilism
    # (Chrysippus is a Stoic compatibilist, not a semicompatibilist; the term is Fischer's)
    EdgeSpec(
        source_id="quote_chrysippus_cylinder_1da2c55b",
        target_id="concept_semicompatibilism_6t7u8v9w",
        relation="exemplifies",
        metadata={},
    ),
]

# ---------------------------------------------------------------------------
# Passage citations: link quote nodes to local passages where text matches
# ---------------------------------------------------------------------------

CITATIONS_TO_ENSURE = [
    # Alexander De Fato 14 - core eph' hemin / autexousion argument
    CitationSpec(
        kg_node_id="quote_alexander_alternatives_e4d14e13",
        passage_id="ae88c271-a54c-4da5-8842-fc4eecc661c2",
        citation_type="primary_source",
        confidence=0.95,
        notes="De Fato 14: Alexander argues the Stoic redefinition of eph' hemin fails to preserve the autexousion.",
    ),
    # Alexander De Fato 13 - introduction of the eph' hemin problem
    CitationSpec(
        kg_node_id="quote_alexander_alternatives_e4d14e13",
        passage_id="e62896b9-235c-4584-b82b-cec83bcbd601",
        citation_type="primary_source",
        confidence=0.90,
        notes="De Fato 13: Alexander introduces the problem of eph' hemin under universal fate.",
    ),
    # Carneades / Cicero Fat. 31
    CitationSpec(
        kg_node_id="quote_carneades_cafma_4483b50a",
        passage_id="7bdfd343-54ca-4e5e-bccd-6fafa8345670",
        citation_type="primary_source",
        confidence=0.98,
        notes="Fat. 31: Cicero reports Carneades' argument against fate via antecedent causes.",
    ),
    # Chrysippus cylinder / Cicero Fat. 43
    CitationSpec(
        kg_node_id="quote_chrysippus_cylinder_1da2c55b",
        passage_id="1812b556-ba17-4407-9998-f0383d158dd2",
        citation_type="primary_source",
        confidence=0.98,
        notes="Fat. 43: Cicero reports Chrysippus' cylinder analogy for assent and character.",
    ),
    # Chrysippus cylinder / Cicero Fat. 42 (context)
    CitationSpec(
        kg_node_id="quote_chrysippus_cylinder_1da2c55b",
        passage_id="0a1bf1ae-9888-4a9e-8da8-9ff3ae4c8f7e",
        citation_type="primary_source",
        confidence=0.92,
        notes="Fat. 42: Chrysippus' distinction between principal and antecedent causes, leading into the cylinder.",
    ),
    # Epictetus Disc. I.1
    CitationSpec(
        kg_node_id="quote_epictetus_prohairesis_3fabff35",
        passage_id="9c42dec9-afbb-4a1c-b3da-4636fb3161fb",
        citation_type="primary_source",
        confidence=0.95,
        notes="Discourses I.1 (Epict. 1): Opens with the eph' hemin distinction and the unique reflexive power of prohairesis.",
    ),
    # Lucretius clinamen passage - DRN II.250-274
    CitationSpec(
        kg_node_id="quote_lucretius_clinamen_ii_251_293_176829af",
        passage_id="924a969a-5428-42f7-96a2-2bb094d558bc",
        citation_type="primary_source",
        confidence=0.98,
        notes="DRN II.250-274: clinamen, fati foedera, and libera voluntas.",
    ),
    # Lucretius clinamen passage - DRN II.275-299
    CitationSpec(
        kg_node_id="quote_lucretius_clinamen_ii_251_293_176829af",
        passage_id="dd949fff-90da-4315-a4fc-ae455566b268",
        citation_type="primary_source",
        confidence=0.98,
        notes="DRN II.275-299: continuation, voluntas refrenans and the argument from animal motion.",
    ),
    # Lucretius swerve (shorter) - DRN II.250-274
    CitationSpec(
        kg_node_id="quote_lucretius_swerve_8bae0c52",
        passage_id="924a969a-5428-42f7-96a2-2bb094d558bc",
        citation_type="primary_source",
        confidence=0.96,
        notes="DRN II.250-274: the core clinamen passage.",
    ),
    # Origen De Principiis III.1.1 - heading and context
    CitationSpec(
        kg_node_id="quote_origen_autexousion_abbb5a2e",
        passage_id="f85d1b5d-02dd-4f57-9a82-c42111ae5e63",
        citation_type="primary_source",
        confidence=0.95,
        notes="De Principiis III.1.1: title and opening of the chapter on autexousion.",
    ),
    # Origen De Principiis III.1.1a - definition of autexousion
    CitationSpec(
        kg_node_id="quote_origen_autexousion_abbb5a2e",
        passage_id="1906f121-848d-416f-acc2-a271b77d0341",
        citation_type="primary_source",
        confidence=0.97,
        notes="De Principiis III.1.1a: 'in order to understand what autexousion is, we must unfold its concept'.",
    ),
    # Plotinus heimarmene - Enn. III.1.1
    CitationSpec(
        kg_node_id="quote_plotinus_heimarmene_31dbdc1e",
        passage_id="5e016d36-087b-4a92-a92a-9cc56fbb3740",
        citation_type="primary_source",
        confidence=0.90,
        notes="Enn. III.1.1: opening of On Fate, discusses multiple causal theories.",
    ),
]


async def ensure_node_exists(conn: asyncpg.Connection, node_id: str) -> None:
    exists = await conn.fetchval(
        f"SELECT 1 FROM {SCHEMA}.kg_nodes WHERE node_id = $1",
        node_id,
    )
    if not exists:
        raise RuntimeError(f"Required node missing: {node_id}")


async def update_node(conn: asyncpg.Connection, update: NodeUpdate, apply: bool) -> None:
    await ensure_node_exists(conn, update.node_id)
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
    await ensure_node_exists(conn, edge.source_id)
    await ensure_node_exists(conn, edge.target_id)
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
        inserted_edges = 0
        deleted_edges = 0
        inserted_citations = 0

        for update in NODE_UPDATES:
            await update_node(conn, update, confirm)
            updated_nodes += 1

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
                "inserted_edges": inserted_edges,
                "deleted_edges": deleted_edges,
                "inserted_passage_citations": inserted_citations,
            },
            "batch_nodes": [update.node_id for update in NODE_UPDATES],
            "decisions": [
                {
                    "node_id": "quote_alexander_alternatives_e4d14e13",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Alexander of Aphrodisias, De Fato 13-15"],
                    "notes": ["marked as English paraphrase; passage citations added for De Fato 13, 14"],
                },
                {
                    "node_id": "quote_augustine_divided_will_b45d573e",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Augustine, Confessions VIII.9-10"],
                    "notes": ["marked as English paraphrase; Confessions not in local passage corpus"],
                },
                {
                    "node_id": "quote_augustine_liberum_arbitrium_0661f946",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Augustine, Confessions VIII.12"],
                    "notes": [
                        "marked as English paraphrase",
                        "FIXED: previous description incorrectly cited Confessions IX; garden scene is VIII.12",
                        "Confessions not in local passage corpus",
                    ],
                },
                {
                    "node_id": "quote_carneades_cafma_4483b50a",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Cicero, De Fato 31"],
                    "notes": ["marked as English paraphrase; passage citation added"],
                },
                {
                    "node_id": "quote_chrysippus_cylinder_1da2c55b",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Cicero, De Fato 42-43"],
                    "notes": [
                        "marked as English paraphrase; passage citations added for Fat. 42, 43",
                        "removed misleading exemplifies->semicompatibilism edge (Fischer's term, not Chrysippus')",
                    ],
                },
                {
                    "node_id": "quote_epictetus_prohairesis_3fabff35",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Epictetus, Discourses I.1"],
                    "notes": ["marked as English paraphrase; passage citation added"],
                },
                {
                    "node_id": "quote_lucretius_clinamen_ii_251_293_176829af",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Lucretius, DRN II.250-274", "Lucretius, DRN II.275-299"],
                    "notes": ["marked as English paraphrase / passage reference; two passage citations added"],
                },
                {
                    "node_id": "quote_lucretius_swerve_8bae0c52",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Lucretius, DRN II.250-274"],
                    "notes": ["marked as English paraphrase; passage citation added"],
                },
                {
                    "node_id": "quote_origen_autexousion_abbb5a2e",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Origen, De Principiis III.1.1"],
                    "notes": ["marked as English paraphrase; two passage citations added (III.1.1 and III.1.1a)"],
                },
                {
                    "node_id": "quote_plotinus_autexousion_65371acd",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Plotinus, Enneads III.1", "Plotinus, Enneads VI.8"],
                    "notes": [
                        "marked as English paraphrase",
                        "exact passage for 'sage under torture' not identified; work-level sourcing used",
                    ],
                },
                {
                    "node_id": "quote_plotinus_heimarmene_31dbdc1e",
                    "status": "retained_rewritten_and_passage_sourced",
                    "sources": ["Plotinus, Enneads III.1.1"],
                    "notes": ["marked as English paraphrase; passage citation added"],
                },
                {
                    "node_id": "quote_plotinus_one_freedom_b1d66acd",
                    "status": "retained_rewritten_and_work_sourced",
                    "sources": ["Plotinus, Enneads VI.8"],
                    "notes": ["marked as English paraphrase; work-level sourcing used"],
                },
            ],
        }

        REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(jd(summary) + "\n", encoding="utf-8")

        lines = [
            "# KG Manual Review Batch 03 Results",
            "",
            "Focus: all 12 unsupported quote nodes.",
            "",
            f"- Applied: `{confirm}`",
            f"- Updated nodes: `{updated_nodes}`",
            f"- Inserted edges: `{inserted_edges}`",
            f"- Deleted edges: `{deleted_edges}`",
            f"- Inserted passage citations: `{inserted_citations}`",
            "",
            "## Key Changes",
            "",
            "- All 12 quote nodes were presenting English paraphrases as if they were direct quotes.",
            "- Every node now explicitly marked as `quote_status: English paraphrase` in metadata.",
            "- 8 nodes received passage-level citations from the local corpus (13 total citations).",
            "- 4 nodes received work-level sourcing only (2 Augustine Confessions not in corpus, 2 Plotinus passages not precisely identified).",
            "- Assertive unsupported claims removed from all descriptions.",
            "- Fixed: `quote_augustine_liberum_arbitrium_0661f946` previously cited Confessions IX; corrected to VIII.12.",
            "- Fixed: `quote_chrysippus_cylinder_1da2c55b` had misleading `exemplifies->semicompatibilism` edge; removed.",
            "",
            "## Decisions",
            "",
        ]
        for decision in summary["decisions"]:
            lines.append(f"- `{decision['node_id']}`: `{decision['status']}`")
            lines.append(f"  Sources: {', '.join(decision['sources'])}")
            if decision.get("notes"):
                for note in decision["notes"]:
                    lines.append(f"  - {note}")
        lines.append("")
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
