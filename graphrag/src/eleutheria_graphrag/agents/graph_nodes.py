"""
pydantic-graph nodes and shared helpers for the scholarly GraphRAG pipeline.

The production (react-mode) pipeline uses the nodes defined here:

    ClassifyQueryType
      -> [agent loop, see react_loop.py]
      -> DraftClaimLedger
      -> RenderGroundedAnswer
      -> ProgrammaticVerify
      -> End

together with ``assess_evidence_sufficiency`` and the helper functions in
this module. The FSM-only middle nodes (ExpandQuery, DiscoverCorpus,
BuildResearchNotebook, PlanReading, TreeNavigateWorks, ExpandEvidenceBundles,
SeekCounterEvidence, the EvidenceSufficiency node shell) and the historical
compatibility wrappers live in ``legacy_fsm_nodes.py``; they import the
shared helpers back from this module.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time as _time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic_graph import BaseNode, End, GraphRunContext

if TYPE_CHECKING:
    from eleutheria_graphrag.agents.legacy_fsm_nodes import ExpandQuery

from eleutheria_graphrag.agents.ancient_text_matching import (
    MODERN_STOPWORDS,
)
from eleutheria_graphrag.agents.ancient_text_matching import (
    contains_word_bounded as _contains_word_bounded,
)
from eleutheria_graphrag.agents.ancient_text_matching import (
    fold_ancient_text as _fold_ancient_text,
)
from eleutheria_graphrag.agents.ancient_text_matching import (
    word_bounded_index as _word_bounded_index,
)
from eleutheria_graphrag.agents.dependencies import Deps
from eleutheria_graphrag.agents.dialectical_synthesis import format_scholar_reference
from eleutheria_graphrag.agents.graph_helpers import (
    node_integrity_status as _node_integrity_status,
)
from eleutheria_graphrag.agents.pipeline_config import (
    QueryType,
    get_pipeline_config,
    query_type_to_complexity,
)
from eleutheria_graphrag.agents.state import (
    Citation,
    ClaimLedgerItem,
    ClaimStatus,
    ContextPack,
    DossierFacet,
    Evidence,
    EvidenceBundle,
    EvidenceLayer,
    EvidenceSource,
    GroundedPosition,
    PassageRef,
    QueryComplexity,
    RAGState,
    ReasoningStep,
    ResearchFacet,
    ResearchNotebook,
    RetrievalBudget,
    ScholarlyAnswer,
    ScholarlyDossier,
    scholar_rag_enabled,
)
from eleutheria_graphrag.agents.structured_models import (
    ClaimLedgerDraft,
    ClaimLedgerDraftItem,
    ClassificationResult,
    CRAGValidation,
    ExpansionTerms,
    SelfRAGEvaluation,
    SufficiencyAssessment,
)
from eleutheria_graphrag.agents.text_utils import truncate_json, truncate_text
from eleutheria_graphrag.agents.text_verifier import extract_greek_runs
from eleutheria_graphrag.services.json_extractor import (
    JSONExtractionError,
    extract_json,
)
from eleutheria_graphrag.services.model_registry import get_model
from eleutheria_graphrag.services.retrieval_strategy import (
    passage_role_condition,
)
from eleutheria_graphrag.services.snapshot_retrieval import (
    db_is_connected,
    linked_passage_rows,
    translation_for_passage,
)

logger = logging.getLogger(__name__)


def _append_reasoning_step(
    state: RAGState,
    node_name: str,
    model: str | None,
    prompt_summary: str,
    full_prompt_tokens: int,
    raw_output: str,
    thinking: str | None = None,
    parsed_result: dict[str, Any] | None = None,
    skipped: bool = False,
    skip_reason: str | None = None,
    duration_ms: int = 0,
) -> None:
    """Append a ReasoningStep to the state's reasoning trace."""
    state.reasoning_trace.append(
        ReasoningStep(
            node_name=node_name,
            timestamp_ms=int(_time.time() * 1000),
            duration_ms=duration_ms,
            model=model,
            prompt_summary=prompt_summary[:200],
            full_prompt_tokens=full_prompt_tokens,
            raw_output=raw_output,
            thinking=thinking,
            parsed_result=parsed_result,
            skipped=skipped,
            skip_reason=skip_reason,
        )
    )


def _proof_chain_for_inferred(
    state: RAGState,
    deps: Deps,
    subject_id: str,
    object_id: str,
) -> list[dict[str, Any]]:
    """Return a JSON-safe proof chain for any inferred edge ``subject -> object``.

    Looks up entries previously recorded by the ontology-aware retrieval
    layer in ``state.inferred_edges``. For each match, constructs a minimal
    rdflib graph containing only the asserted reverse triple (the premise
    we already know exists, since the inferred edge is its inverseOf
    derivative) and runs :func:`build_proof_chain`. Multiple inferred
    relations between the same pair yield multiple steps in the returned
    list.

    Returns an empty list when no inferred edge links the pair, keeping
    ``ClaimLedgerItem.proof_chain`` ``None`` for directly-asserted claims.
    """
    inferred = getattr(state, "inferred_edges", None)
    if not inferred:
        return []

    matches = [t for t in inferred if t[0] == subject_id and t[2] == object_id]
    if not matches:
        return []

    try:
        from rdflib import Graph

        from eleutheria_kg.semantic.inference import TRANSITIVE_PROPERTIES
        from eleutheria_kg.semantic.proof import (
            build_proof_chain,
            serialize_proof_chain,
        )
        from eleutheria_kg.semantic.vocab import (
            CLEAN_INVERSE_PAIRS,
            edge_property,
            mint_node_iri,
        )
    except Exception:  # noqa: BLE001 — semantic layer optional in some tests
        logger.warning(
            "semantic layer unavailable; skipping proof chain", exc_info=True
        )
        return []

    inverse_index: dict[str, str] = {}
    for a, b in CLEAN_INVERSE_PAIRS:
        inverse_index.setdefault(a, b)
        inverse_index.setdefault(b, a)

    # Build focused subgraphs from deps.outgoing_edges, never a full rdflib load.
    subj_iri = mint_node_iri(subject_id)
    obj_iri = mint_node_iri(object_id)
    outgoing = getattr(deps, "outgoing_edges", {}) or {}

    chain_steps: list[dict[str, Any]] = []
    for s_id, derived_rel, o_id in matches:
        premise_rel = inverse_index.get(derived_rel)
        if premise_rel:
            # The asserted premise is ``(o_id, premise_rel, s_id)`` — verify
            # it really is in the edge dicts before claiming a proof.
            premise_asserted = any(
                edge.get("relation") == premise_rel
                and (edge.get("target") or edge.get("target_id", "")) == s_id
                for edge in outgoing.get(o_id, [])
            )
            if premise_asserted:
                graph = Graph()
                graph.add(
                    (
                        mint_node_iri(o_id),
                        edge_property(premise_rel),
                        mint_node_iri(s_id),
                    )
                )
                steps = build_proof_chain(
                    graph,
                    (subj_iri, edge_property(derived_rel), obj_iri),
                )
                chain_steps.extend(serialize_proof_chain(steps))
                continue

        prop = edge_property(derived_rel)
        if prop not in TRANSITIVE_PROPERTIES:
            continue
        graph = Graph()
        for source_id, edges in outgoing.items():
            for edge in edges:
                if edge.get("relation") != derived_rel:
                    continue
                target_id = edge.get("target") or edge.get("target_id", "")
                if target_id:
                    graph.add(
                        (mint_node_iri(source_id), prop, mint_node_iri(target_id))
                    )
        steps = build_proof_chain(graph, (subj_iri, prop, obj_iri))
        chain_steps.extend(serialize_proof_chain(steps))

    return chain_steps


def _attach_proof_chains(
    state: RAGState,
    deps: Deps,
    claims: list[ClaimLedgerItem],
) -> int:
    """Mutate ``claims`` in place, attaching ``proof_chain`` where applicable.

    A claim qualifies when any inferred edge in ``state.inferred_edges``
    connects two of its supporting evidence node IDs. The proof chain is
    serialized via :func:`serialize_proof_chain`. Also appends a
    ``ReasoningStep`` for each newly-attached chain so the trace surfaces
    the derivation. Returns the number of claims that received a chain.
    """
    inferred = getattr(state, "inferred_edges", None)
    if not inferred:
        return 0

    attached = 0
    for claim in claims:
        if not claim.evidence_ids:
            continue
        evidence_set = set(claim.evidence_ids)
        chain_parts: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for s_id, rel, o_id in inferred:
            if s_id == o_id:
                continue
            if s_id not in evidence_set or o_id not in evidence_set:
                continue
            key = (s_id, rel, o_id)
            if key in seen:
                continue
            seen.add(key)
            chain_parts.extend(_proof_chain_for_inferred(state, deps, s_id, o_id))
        if chain_parts:
            claim.proof_chain = chain_parts
            attached += 1
            _append_reasoning_step(
                state,
                "DraftClaimLedger:proof_chain",
                None,
                f"derived via inverseOf for claim: {claim.claim[:120]}",
                0,
                "",
                parsed_result={
                    "steps": chain_parts,
                    "evidence_ids": list(claim.evidence_ids),
                },
            )
    return attached


def _resolve_model_api_id(state: RAGState) -> str | None:
    """Return the explicit ``model_override`` for the selected model.

    ``None`` means "let the provider loop choose", which is what an unknown
    selection should do.
    """
    try:
        return get_model(state.selected_model).api_id
    except KeyError:
        return None


DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
LINE_SPLIT_RE = re.compile(r"\n+")
REF_RE = re.compile(r"\[(.*?)\]")
REF_NUMBER_RE = re.compile(r"\b\d+\b")
# Paired quotation marks: straight/curly double, curly single, guillemets
# (double and single), German low-9 variants. One capture group per pair.
QUOTE_RE = re.compile(
    r"[\"“](.+?)[\"”]"
    r"|‘(.+?)’"
    r"|«\s*(.+?)\s*»"
    r"|‹\s*(.+?)\s*›"
    r"|„(.+?)[“”]"
    r"|‚(.+?)[‘’]"
)
GREEK_CHAR_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")
ELLIPSIS_RE = re.compile(r"…|⋯|\.{3,}")
# Chunks worth checking independently inside a blockquote line: the quoted
# matter itself vs. dash/parenthesis attributions ("— Cicero, De Fato 20").
LATIN_CHUNK_SPLIT_RE = re.compile(r"[—–()\[\]]|\s-\s")
# MODERN_STOPWORDS (the modern-language function-word gate for candidate
# ancient Latin) lives in ``ancient_text_matching`` — shared with the
# post-synthesis text verifier. Imported above.
TERM_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ\u0370-\u03FF\u1F00-\u1FFF']+")
STOP_TERMS = {
    "about",
    "above",
    "after",
    "against",
    "also",
    "and",
    "anglais",
    "avec",
    "been",
    "between",
    "dans",
    "de",
    "des",
    "did",
    "does",
    "english",
    "for",
    "from",
    "greek",
    "into",
    "latin",
    "les",
    "mais",
    "more",
    "plus",
    "pour",
    "quote",
    "sur",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "those",
    "through",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
}
DOCTRINAL_HINTS = {
    "account",
    "argued",
    "believe",
    "belief",
    "believed",
    "doctrine",
    "held",
    "position",
    "positions",
    "teach",
    "teaching",
    "theory",
    "view",
    "views",
}
TRANSLATION_HINTS = {
    "english",
    "translation",
    "translate",
    "translated",
    "francais",
    "french",
    "traduction",
}
ORIGINAL_LANGUAGE_HINTS = {
    "greek",
    "grec",
    "latin",
    "latine",
    "original",
}
RESEARCH_STAGE_SEQUENCE: list[tuple[str, str]] = [
    ("classify_query", "Classify query"),
    ("expand_query", "Expand query"),
    ("discover_corpus", "Discover corpus"),
    ("research_notebook", "Build research notebook"),
    ("reading_plan", "Plan reading"),
    ("scholarly_dossier", "Assemble scholarly dossier"),
    ("tree_navigation", "Navigate works"),
    ("evidence_bundles", "Expand evidence bundles"),
    ("counter_evidence", "Seek counter-evidence"),
    ("context_pack", "Pack long context"),
    ("evidence_sufficiency", "Check evidence sufficiency"),
    ("draft_claim_ledger", "Draft claim ledger"),
    ("render_grounded_answer", "Render grounded answer"),
    ("scholarly_polish", "Scholarly polish"),
    ("programmatic_verify", "Programmatic verify"),
]

SYSTEM_PROMPT = """\
You are a specialist in ancient philosophy writing for a scholarly audience. \
Your answers should read like sections from a peer-reviewed article or a \
Cambridge Companion chapter — detailed, nuanced, and richly documented.

Rules:
- Work like a careful philologist: frame the question, inspect the textual \
  tradition, gather primary evidence, seek counter-evidence, then argue your thesis.
- ALWAYS present ancient text in the format:
  > Greek/Latin original (Author, *Work* canonical_ref)
  > "English translation"
  This dual-language quotation format is mandatory for every primary source citation.
- Never invent Greek or Latin. Quote ONLY text from the evidence bundles.
- Treat doctrinal claims as passage-first. Knowledge-graph metadata may support \
  authorship, chronology, school affiliation, and edition details.
- If the evidence is partial or the textual tradition fragmentary, say so explicitly. \
  Distinguish clearly between direct quotation, paraphrase of lost works (via \
  doxographers), and modern scholarly reconstruction.
- Every substantive claim must carry one or more reference markers.
- Aim for DEPTH over breadth: it is better to analyze 3 passages in detail than \
  to mention 10 superficially.
- Give the full scholarly reference: Author, *Work* Book.Chapter.Section (Edition).
"""

CLASSIFY_QUERY_TYPE_PROMPT = """\
Classify the following question about ancient philosophy into one query type.

Allowed values:
- specific_entity
- global_abstract
- multi_hop
- comparative
- temporal

Return only JSON:
{{"query_type": "...", "confidence": 0.0-1.0, "reason": "...", "complexity": "simple|medium|complex"}}

Question: {question}
"""

EXPAND_QUERY_PROMPT = """\
You are framing a scholarly search query on ancient philosophy.

Return only JSON with:
- expanded_query
- greek_terms: [{{"greek", "transliteration", "translation"}}]
- latin_terms: [{{"latin", "translation"}}]
- philosophers
- concepts
- schools
- periods

Question: {question}
"""

FRAME_RESEARCH_PROMPT = """\
You are opening a research notebook for an ancient philosophy query.

Question: {question}
Retrieved corpus scope:
{corpus_scope}

Return only JSON with:
- question_frame
- facets: [{{"facet_id", "title", "question", "keywords", "required_support", "priority"}}]
- sub_questions
- competing_hypotheses
- open_questions
"""

READING_PLAN_PROMPT = """\
You are planning a scholarly reading order for a structured retrieval system.

Question frame: {question_frame}
Candidate works:
{work_titles}

Facets:
{facets_json}

Return only JSON:
{{"work_titles": ["..."], "facet_ids": ["..."], "rationale": "..."}}
"""

TREE_NAVIGATION_PROMPT = """\
You are navigating a hierarchical index of an ancient work.

Question: {question}
Work: {work_title} by {author}
Current sections:
{sections_json}

Select the sections most worth reading next. Prefer direct evidence and broad
coverage over narrow redundancy.

Return only JSON:
{{"selected_nodes": [{{"work_id": "...", "node_id": "...", "title": "...", "path": "...", "reason": "...", "priority": 1}}], "reasoning": "..."}}
"""

COUNTER_EVIDENCE_PROMPT = """\
You are checking whether the current reading notes contain counter-evidence or
important nuance.

Question frame: {question_frame}
Hypotheses:
{hypotheses}

Bundles:
{bundles_json}

Return only JSON:
{{"bundle_ids": ["bundle-id"], "rationale": "..."}}
"""

SUFFICIENCY_PROMPT = """\
Assess whether the current evidence bundle set is sufficient to answer the
question responsibly.

Question: {question}
Primary bundles: {bundle_count}
Distinct works: {work_count}
Counter-evidence notes: {counter_count}
Notebook open questions: {open_questions}

Return only JSON:
{{"score": 0.0-1.0, "sufficient": true, "reason": "...", "refinement": "..."}}
"""

CLAIM_LEDGER_PROMPT = """\
Build a claim ledger for a scholarly answer.

Question: {question}
Grounding policy: {grounding_policy}
Notebook:
{notebook_json}

Dossier:
{dossier_json}

Evidence catalog:
{evidence_catalog_json}

Context:
{context}

Rules:
- Cover the highest-priority dossier facets before adding lower-value claims.
- Prefer 1 synthesis claim plus 1 textual anchor claim for the strongest facets when evidence allows.
- If no direct text survives for a facet, say explicitly that the surviving evidence is testimonial or doxographic.
- In evidence_ids, return the exact evidence_id values from the evidence catalog, not display refs like "P1" or "25".
- Use passage evidence_ids for doctrinal or textual claims whenever possible.
- Use metadata evidence_ids only for bibliographic/context claims.
- Set evidence_class to one of: direct_text, ancient_testimony, metadata, counter_evidence.
- Return 8-15 claims when evidence permits, and never more than 18. More claims = richer answer.
- Keep each claim to 1-2 sentences.
- Include quote_original and quote_translation for EVERY claim that has direct textual evidence. \
  Quotes may be up to 400 characters each — longer quotations produce better scholarly answers.
- Always include canonical_ref (e.g. "III.1.5", "617e", "II.20") in the claim text when available.
- Keep the ledger organized around facets rather than retrieval order.

Return only JSON:
{{"claims": [{{"claim": "...", "evidence_ids": ["..."], "facet_id": "...", "evidence_class": "direct_text|ancient_testimony|metadata|counter_evidence", "quote_original": "...", "quote_translation": "...", "support_type": "passage|metadata", "confidence": 0.0-1.0, "status": "supported|insufficient"}}]}}
"""

RENDER_ANSWER_PROMPT = """\
You are writing a scholarly article section on ancient philosophy. Your answer must \
read like a Cambridge Companion chapter — deeply grounded in the primary texts, with \
philological precision and philosophical argumentation.

Question: {question}
Claim ledger:
{ledger_json}

Dossier:
{dossier_json}

Reference map:
{reference_json}

Evidence packet (FULL PASSAGE TEXTS — use these for exegesis):
{evidence_packet_json}

## MANDATORY STRUCTURE

### 1. Thesis (1 paragraph, 4-6 sentences)
Frame the scholarly question, state your main argument, and preview the key \
textual evidence you will analyze.

### 2. For EACH major passage in the evidence packet, write a full exegesis section:

**This is the heart of the answer. For each important passage, you MUST follow \
this exact pattern:**

a) **Quote the passage** in the mandatory dual-language format:
   > Original Greek/Latin text (Author, *Work* canonical_ref) [reference_marker]
   > "English translation"

b) **Philological analysis** (1-2 sentences): Analyze the key terms in the passage. \
   What does this specific word/phrase mean in context? (e.g., "The term αὐτεξούσιον, \
   literally 'self-empowered', is Origen's preferred translation of the Stoic τὸ ἐφ' ἡμῖν...")

c) **Argumentative analysis** (2-4 sentences): What is the logical structure of the \
   argument? How does the author reason? What premises lead to what conclusion?

d) **Connection to the question** (1-3 sentences): Explicitly state how this passage \
   answers or illuminates the question asked. Be specific — do not just say "this is relevant."

### 3. Synthesis and comparison (1-2 paragraphs)
After analyzing the individual passages, synthesize: What do the texts reveal when \
read together? Where do the thinkers agree, diverge, or develop each other's ideas?

### 4. Caveats and limitations (1 short paragraph)
Note gaps in the evidence, textual transmission problems, or scholarly debates.

## REQUIREMENTS — doctoral chapter, not a journal summary
- Cover at least {required_sections} dossier-driven exegesis sections, including an \
  opening orientation and a closing scholarly assessment. **Use `### Section Title` \
  markdown headings (H3) — not bold lines, not plain prose** so the reader can navigate.
- Include at least {required_quote_blocks} quotation blocks with original + translation, \
  drawn from the dossier — never invent.
- Target **1500-2500 words per exegesis section** (~10,000-15,000 chars total for a \
  6-section answer; ~18,000-25,000 chars for an 8-10 section answer). A thesis \
  chapter section is dense, layered prose; if you find yourself writing in summaries, \
  add a paragraph of philological analysis, a paragraph of doxographical context, and \
  a paragraph of scholarly debate.
- Embed at least **4 inline citation markers per section** (e.g. `[P1]`, `[N3]`), placed \
  immediately after the specific claim they ground, never bunched at the end.
- For each substantive section, include **at least 3 primary-source block quotes** in the \
  mandatory dual-language format (original + translation), each followed by 4-8 sentences \
  of philological and argumentative analysis (key terms, syntactic structure, \
  argument shape, doxographical parallels, scholarly debate).
- EVERY passage in the evidence packet with Greek/Latin text SHOULD be quoted and analyzed.
- Use the reference markers from the reference map (e.g., [P1], [N3]).
- Also include scholarly references in prose: "as Origen writes in *De Principiis* III.1.5 [P2]..."
- Never invent Greek, Latin, or translations. Quote ONLY from the evidence packet.
- Distinguish between direct text, ancient testimony, and your own synthesis.

## EXAMPLE OF THE EXPECTED REGISTER AND DEPTH (excerpt of a single section)

### 2. Chrysippus on perfect and auxiliary causes

Chrysippus's response to the Lazy Argument turns on a taxonomy of causes that \
distinguishes the *perfect and principal* (αἴτιον αὐτοτελὲς καὶ προηγούμενον) from \
*auxiliary and proximate* causes (αἴτια συνεργὰ καὶ προσεχῆ) [P3]. Cicero preserves \
the technical vocabulary in *De Fato* 41:

  > "causarum enim aliae sunt perfectae et principales, aliae adiuvantes et proximae" \
  > (Cicero, *De Fato* 41) [P3]
  > "for some causes are perfect and principal, others auxiliary and proximate"

The Latin pair *perfectae et principales* renders, on Sharples's reading, the Stoic \
τέλειον καὶ προηγούμενον [P3]; the contrast term *adiuvantes* (auxiliary) tracks \
συνεργόν. Chrysippus's point is that fate operates through the perfect causes — the \
agent's own assent (συγκατάθεσις) — and not as a brute external compulsion mediated \
by auxiliary stimuli [P4]. This taxonomy is the philosophical engine of the cylinder \
analogy: the push is auxiliary, the cylinder's shape is principal [P4].

Bobzien argues that this distinction does not collapse into a modern compatibilism \
[N1]: what is "up to us" (τὸ ἐφ' ἡμῖν) is not the libertarian power to do otherwise, \
but the fact that the principal cause of assent is internal to the agent's rational \
nature [N1]. Frede, by contrast, reads the same passages as preparing the ground for \
a notion of *moral* freedom that will be developed by Epictetus [N2]...

(Each section continues at this density for 800-1200 words.)
"""

SCHOLARLY_POLISH_PROMPT = """\
You are performing a final scholarly prose pass on an already grounded answer. \
The goal is to make this read like a published academic article with deep textual exegesis.

Question: {question}
Dossier:
{dossier_json}

Draft answer:
{draft_answer}

Rules:
- Preserve every existing citation marker and reference EXACTLY.
- Do not introduce any new fact not already in the draft or dossier.
- For each passage quotation, ensure there is EXEGESIS after it:
  (a) philological analysis of key terms
  (b) explanation of the argument structure
  (c) explicit connection to the question asked
  If the draft just quotes a passage and moves on, ADD the analysis.
- EXPAND compressed sections: if a section is only 1-2 sentences, develop the \
  argument into 2-3 paragraphs analyzing the evidence already cited.
- Ensure every quotation block uses the dual-language format:
  > Original text (Author, *Work* ref)
  > "English translation"
- The final answer should be 2000-4000 words. If the draft is shorter, expand \
  the exegesis of existing passages — do not add new facts.
- Keep Greek/Latin quotes verbatim. Keep all reference markers.
"""

EXPAND_RETRY_PROMPT = """\
Your previous scholarly draft was only {current_chars} characters across \
{current_sections} sections. Expand it to at least {target_chars} characters by \
deepening the exegesis you already have. Do NOT add new claims or new evidence — \
work only from the dossier and evidence packet below.

Question: {question}

Dossier:
{dossier_json}

Evidence packet (FULL passage texts — quote these verbatim):
{evidence_packet_json}

Reference map:
{reference_json}

Previous draft:
{draft_answer}

Expansion strategy (apply to EACH section):
1. Add a paragraph of philological + textual analysis per claim — unpack key Greek \
   or Latin terms, explain the argument structure, connect to the question.
2. Quote at least 2 primary passages verbatim per section in the mandatory \
   dual-language block-quote format (original + translation), each followed by \
   2-4 sentences of exegesis.
3. Engage with at least 1 scholar's counter-position per section — name them, \
   summarise their reading in 2-3 sentences, then accept or rebut.
4. Target {target_chars}+ chars total, ~800-1200 words per section.

Hard rules:
- Preserve every existing citation marker and reference EXACTLY.
- Do not introduce any new fact, citation marker, or quotation that is not \
  already present in the dossier, evidence packet, or previous draft.
- Keep all original Greek/Latin verbatim. Never paraphrase ancient text.
- Output the rewritten Markdown only.
"""

COMPRESSION_REPAIR_PROMPT = """\
You are repairing a grounded scholarly answer that is too compressed relative to the dossier.

Question: {question}
Required sections: {required_sections}
Required quotation blocks: {required_quote_blocks}
Facet titles:
{facet_titles}

Dossier:
{dossier_json}

Claim ledger:
{ledger_json}

Current answer:
{draft_answer}

Rules:
- Expand coverage so the answer actually reflects the dossier.
- Preserve every existing citation marker exactly.
- Use only evidence already present in the dossier or claim ledger.
- Keep a short thesis paragraph, then multiple titled sections with blank lines between them.
- Include quotation blocks when quoted evidence is available.
- Distinguish direct text, testimony, and synthesis instead of blending them.
- Do not add any uncited sentence.
"""

CLAIM_LEDGER_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["claims"],
    "properties": {
        "claims": {
            "type": "array",
            "maxItems": 12,
            "items": {
                "type": "object",
                "required": [
                    "claim",
                    "evidence_ids",
                    "facet_id",
                    "evidence_class",
                    "quote_original",
                    "quote_translation",
                    "support_type",
                    "confidence",
                    "status",
                ],
                "properties": {
                    "claim": {"type": "string"},
                    "evidence_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "facet_id": {"type": ["string", "null"]},
                    "evidence_class": {
                        "type": "string",
                        "enum": [
                            "direct_text",
                            "ancient_testimony",
                            "metadata",
                            "counter_evidence",
                        ],
                    },
                    "quote_original": {"type": ["string", "null"]},
                    "quote_translation": {"type": ["string", "null"]},
                    "support_type": {
                        "type": "string",
                        "enum": ["passage", "metadata"],
                    },
                    "confidence": {"type": "number"},
                    "status": {
                        "type": "string",
                        "enum": ["supported", "insufficient"],
                    },
                },
            },
        }
    },
}

_STATIC_GREEK_TERMS = {
    "fate": {
        "greek_terms": [
            {
                "greek": "εἱμαρμένη",
                "transliteration": "heimarmene",
                "translation": "fate",
            }
        ],
        "concepts": ["fate"],
    },
    "assent": {
        "greek_terms": [
            {
                "greek": "συγκατάθεσις",
                "transliteration": "sunkatathesis",
                "translation": "assent",
            }
        ],
        "concepts": ["assent"],
    },
    "prohairesis": {
        "greek_terms": [
            {
                "greek": "προαίρεσις",
                "transliteration": "prohairesis",
                "translation": "moral choice",
            }
        ],
        "concepts": ["prohairesis"],
    },
}


def _parse_json(text: str) -> Any:
    """Extract JSON from LLM output, stripping markdown code fences.

    Delegates to :func:`eleutheria_graphrag.services.json_extractor.extract_json`
    so model outputs that wrap JSON in code fences, prefix it with
    natural-language reasoning, or trail prose after the closing brace are
    all recovered. Raises ``json.JSONDecodeError`` for backward-compat with
    the prior contract.
    """
    try:
        return extract_json(text)
    except JSONExtractionError as exc:
        raise json.JSONDecodeError(str(exc), text or "", 0) from exc


def _coerce_claim_ledger_payload(payload: Any) -> ClaimLedgerDraft:
    if isinstance(payload, list):
        payload = {"claims": payload}
    return ClaimLedgerDraft.model_validate(payload)


def _salvage_claim_ledger(raw: str) -> ClaimLedgerDraft | None:
    """Recover fully formed claim objects from truncated JSON output."""
    try:
        text = raw.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*)", text)
        if match:
            text = match.group(1).strip()
        claims_anchor = text.find('"claims"')
        if claims_anchor == -1:
            return None
        array_start = text.find("[", claims_anchor)
        if array_start == -1:
            return None

        objects: list[ClaimLedgerDraftItem] = []
        in_string = False
        escape = False
        depth = 0
        obj_start: int | None = None

        for index, char in enumerate(text[array_start:], start=array_start):
            if escape:
                escape = False
                continue
            if char == "\\" and in_string:
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                if depth == 0:
                    obj_start = index
                depth += 1
            elif char == "}":
                if depth == 0:
                    continue
                depth -= 1
                if depth == 0 and obj_start is not None:
                    candidate = text[obj_start : index + 1]
                    try:
                        parsed = json.loads(candidate)
                        objects.append(ClaimLedgerDraftItem.model_validate(parsed))
                    except Exception:
                        pass
                    obj_start = None

        if objects:
            return ClaimLedgerDraft(claims=objects)
    except Exception:
        return None
    return None


def _tokenize_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for token in TERM_RE.findall(text.lower()):
        normalized = token.strip("'")
        if len(normalized) < 3 or normalized in STOP_TERMS:
            continue
        terms.add(normalized)
    return terms


def _question_terms(state: RAGState) -> set[str]:
    terms: set[str] = set()
    for chunk in [state.question, state.expanded_query or "", *state.sub_queries]:
        terms.update(_tokenize_terms(chunk))
    if state.expansion_terms:
        for field in ("philosophers", "concepts", "schools", "periods"):
            for item in getattr(state.expansion_terms, field, [])[:8]:
                terms.update(_tokenize_terms(str(item)))
        for item in getattr(state.expansion_terms, "greek_terms", [])[:8]:
            terms.update(_tokenize_terms(getattr(item, "greek", "")))
            terms.update(_tokenize_terms(getattr(item, "transliteration", "")))
            terms.update(_tokenize_terms(getattr(item, "translation", "")))
        for item in getattr(state.expansion_terms, "latin_terms", [])[:8]:
            terms.update(_tokenize_terms(getattr(item, "latin", "")))
            terms.update(_tokenize_terms(getattr(item, "translation", "")))
    return terms


def _question_requests_translation(state: RAGState) -> bool:
    terms = _question_terms(state)
    return bool(terms & TRANSLATION_HINTS)


def _question_requests_original(state: RAGState) -> bool:
    terms = _question_terms(state)
    return bool(terms & ORIGINAL_LANGUAGE_HINTS)


def _question_requests_quote(state: RAGState) -> bool:
    haystack = " ".join(
        part
        for part in (state.question, state.expanded_query or "", *state.sub_queries)
        if part
    ).lower()
    return any(
        token in haystack
        for token in ("quote", "quotation", "cite", "citation", "citer")
    )


def _question_reference_numbers(state: RAGState) -> tuple[str, ...]:
    haystack = " ".join(
        part
        for part in (state.question, state.expanded_query or "", *state.sub_queries)
        if part
    )
    return tuple(dict.fromkeys(REF_NUMBER_RE.findall(haystack)))


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "facet"


def _question_school_hints(state: RAGState) -> set[str]:
    hints: set[str] = set()
    haystack = " ".join(
        part
        for part in (state.question, state.expanded_query or "", *state.sub_queries)
        if part
    ).lower()
    school_aliases = {
        "stoic": "stoicism",
        "stoics": "stoicism",
        "stoicism": "stoicism",
        "epicurean": "epicureanism",
        "epicureans": "epicureanism",
        "epicureanism": "epicureanism",
        "peripatetic": "peripatetic",
        "peripatetics": "peripatetic",
        "platonist": "platonism",
        "platonists": "platonism",
        "platonic": "platonism",
        "skeptic": "skepticism",
        "skeptics": "skepticism",
        "skepticism": "skepticism",
    }
    for needle, canonical in school_aliases.items():
        if needle in haystack:
            hints.add(canonical)
    if state.expansion_terms:
        for item in getattr(state.expansion_terms, "schools", [])[:8]:
            if item:
                hints.add(str(item).strip().lower())
    return hints


def _question_author_hints(state: RAGState) -> set[str]:
    hints: set[str] = set()
    if state.expansion_terms:
        for item in getattr(state.expansion_terms, "philosophers", [])[:8]:
            if item:
                hints.add(str(item).strip().lower())
    proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", state.question)
    for item in proper_nouns[:8]:
        hints.add(item.strip().lower())
    return hints


def _make_research_facet(
    *,
    title: str,
    question: str,
    keywords: list[str],
    priority: int,
    required_support: str = "passage",
) -> ResearchFacet:
    return ResearchFacet(
        facet_id=_slugify(title),
        title=title,
        question=question,
        keywords=sorted(dict.fromkeys(keyword for keyword in keywords if keyword)),
        required_support=required_support,
        priority=priority,
    )


def _is_doctrinal_query(state: RAGState) -> bool:
    terms = _question_terms(state)
    school_hints = _question_school_hints(state)
    if state.query_type == QueryType.SPECIFIC_ENTITY:
        return False
    if school_hints and state.query_type in {
        QueryType.GLOBAL_ABSTRACT,
        QueryType.MULTI_HOP,
        QueryType.COMPARATIVE,
    }:
        return True
    return bool(terms & DOCTRINAL_HINTS)


def _default_research_facets(state: RAGState) -> list[ResearchFacet]:
    question = state.question.strip() or "this question"
    terms = _question_terms(state)
    school_hints = _question_school_hints(state)
    doctrinal_query = _is_doctrinal_query(state)
    facets: list[ResearchFacet] = []

    if state.query_type == QueryType.SPECIFIC_ENTITY:
        return [
            _make_research_facet(
                title="Identity and Context",
                question=f"Who is the figure at the center of {question}, and in what context do the sources place them?",
                keywords=["identity", "context", *sorted(terms)[:4]],
                priority=1,
                required_support="metadata",
            ),
            _make_research_facet(
                title="Works and Doctrine",
                question=f"What works or doctrines are directly linked to {question}?",
                keywords=["works", "doctrine", *sorted(terms)[:4]],
                priority=2,
            ),
            _make_research_facet(
                title="Textual Basis",
                question=f"What direct textual evidence best anchors an answer to {question}?",
                keywords=["text", "passage", "evidence", *sorted(terms)[:4]],
                priority=3,
            ),
        ]

    if state.query_type == QueryType.COMPARATIVE:
        facets.extend(
            [
                _make_research_facet(
                    title="Points of Agreement",
                    question=f"Where do the relevant sources converge on {question}?",
                    keywords=["agreement", "shared", *sorted(terms)[:4]],
                    priority=1,
                ),
                _make_research_facet(
                    title="Points of Divergence",
                    question=f"Where do the relevant sources diverge on {question}?",
                    keywords=[
                        "difference",
                        "divergence",
                        "contrast",
                        *sorted(terms)[:4],
                    ],
                    priority=2,
                ),
            ]
        )
    elif state.query_type == QueryType.TEMPORAL:
        facets.extend(
            [
                _make_research_facet(
                    title="Early Position",
                    question=f"What do the earlier sources say about {question}?",
                    keywords=["early", "initial", *sorted(terms)[:4]],
                    priority=1,
                ),
                _make_research_facet(
                    title="Development Over Time",
                    question=f"How does the treatment of {question} develop over time?",
                    keywords=["development", "later", "chronology", *sorted(terms)[:4]],
                    priority=2,
                ),
            ]
        )
    else:
        if doctrinal_query:
            facets.extend(
                [
                    _make_research_facet(
                        title="Core Doctrinal Thesis",
                        question=f"What core thesis do the relevant ancient sources attribute to {question}?",
                        keywords=["doctrine", "thesis", "position", *sorted(terms)[:5]],
                        priority=1,
                    ),
                    _make_research_facet(
                        title="Textual Witnesses",
                        question=f"Which passages or testimonia best preserve the ancient evidence for {question}?",
                        keywords=[
                            "text",
                            "passage",
                            "testimony",
                            "evidence",
                            *sorted(terms)[:5],
                        ],
                        priority=2,
                    ),
                ]
            )
        else:
            facets.extend(
                [
                    _make_research_facet(
                        title="Definition",
                        question=f"How do the sources define or characterize {question}?",
                        keywords=["definition", "characterization", *sorted(terms)[:5]],
                        priority=1,
                    ),
                    _make_research_facet(
                        title="Textual Basis",
                        question=f"What direct passages best ground an answer to {question}?",
                        keywords=["text", "passage", "evidence", *sorted(terms)[:5]],
                        priority=2,
                    ),
                ]
            )

    if terms & {"fate", "heimarmene", "determinism", "causes", "cause", "necessity"}:
        facets.append(
            _make_research_facet(
                title="Causal Mechanism"
                if not doctrinal_query
                else "Causal Structure of Fate",
                question=f"What causal mechanism or explanatory structure do the sources give for {question}?",
                keywords=["cause", "causal", "determinism", "fate", "necessity"],
                priority=2,
            )
        )
    if terms & {
        "responsibility",
        "assent",
        "freedom",
        "choice",
        "prohairesis",
        "moral",
    }:
        facets.append(
            _make_research_facet(
                title="Agency and Responsibility",
                question=f"How do the sources connect {question} to agency, assent, responsibility, or freedom?",
                keywords=[
                    "agency",
                    "assent",
                    "responsibility",
                    "freedom",
                    "choice",
                    "prohairesis",
                ],
                priority=3,
            )
        )
    if doctrinal_query:
        facets.append(
            _make_research_facet(
                title="Ancient Testimony and Preservation",
                question=f"Through which ancient witnesses, reports, or preserved fragments do we know the evidence for {question}?",
                keywords=[
                    "testimony",
                    "preservation",
                    "report",
                    "fragment",
                    *sorted(school_hints),
                ],
                priority=4,
            )
        )
    if school_hints or state.query_type in {
        QueryType.GLOBAL_ABSTRACT,
        QueryType.MULTI_HOP,
        QueryType.COMPARATIVE,
    }:
        facets.append(
            _make_research_facet(
                title="Counterpoint and Nuance"
                if not doctrinal_query
                else "Counterpoints and Limits",
                question=f"What counter-evidence, disagreement, or textual nuance complicates {question}?",
                keywords=[
                    "counterpoint",
                    "nuance",
                    "disagreement",
                    "objection",
                    *sorted(school_hints),
                ],
                priority=4,
            )
        )

    deduped: list[ResearchFacet] = []
    seen: set[str] = set()
    for facet in sorted(facets, key=lambda item: (item.priority, item.title.lower())):
        if facet.facet_id in seen:
            continue
        seen.add(facet.facet_id)
        deduped.append(facet)
    return deduped[:6]


def _normalize_notebook_facets(
    state: RAGState, facets: list[ResearchFacet]
) -> list[ResearchFacet]:
    if not facets:
        return _default_research_facets(state)

    normalized: list[ResearchFacet] = []
    seen: set[str] = set()
    for index, facet in enumerate(facets, start=1):
        facet_id = facet.facet_id or _slugify(
            facet.title or facet.question or f"facet-{index}"
        )
        priority = max(1, min(5, facet.priority or index))
        item = facet.model_copy(
            update={
                "facet_id": facet_id,
                "priority": priority,
                "required_support": facet.required_support or "passage",
            }
        )
        if item.facet_id in seen:
            continue
        seen.add(item.facet_id)
        normalized.append(item)
    return normalized or _default_research_facets(state)


def _author_profile_for_name(state: RAGState, author: str | None) -> dict[str, Any]:
    if not author:
        return {}
    author_norm = re.sub(r"[^a-z0-9]+", " ", author.lower()).strip()
    if not author_norm:
        return {}

    def _match_score(label: str) -> int:
        label_norm = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
        if not label_norm:
            return 0
        if label_norm == author_norm:
            return 100
        if author_norm in label_norm or label_norm in author_norm:
            return 80
        overlap = set(author_norm.split()) & set(label_norm.split())
        return len(overlap) * 10

    best: tuple[int, dict[str, Any]] | None = None
    for evidence in state.all_evidence():
        if evidence.type == "passage":
            continue
        score = _match_score(evidence.label)
        if score <= 0:
            continue
        profile = {
            "label": evidence.label,
            "period": evidence.period,
            "school": evidence.school,
            "role": evidence.role,
            "node_id": evidence.id,
        }
        if best is None or score > best[0]:
            best = (score, profile)
    return best[1] if best else {}


def _bundle_academic_features(
    bundle: EvidenceBundle, state: RAGState
) -> dict[str, Any]:
    profile = _author_profile_for_name(state, bundle.author)
    author_hints = _question_author_hints(state)
    school_hints = _question_school_hints(state)
    label_haystack = " ".join(
        part for part in (bundle.author, bundle.work_title, bundle.section_path) if part
    ).lower()
    author_match = any(hint in label_haystack for hint in author_hints)
    school_value = str(
        profile.get("school") or bundle.metadata.get("author_school") or ""
    ).lower()
    school_match = bool(
        school_hints
        and school_value
        and any(hint in school_value for hint in school_hints)
    )
    work_priority_rank = next(
        (
            index
            for index, title in enumerate(
                state.research_notebook.work_priorities[:20], start=1
            )
            if title.lower() == bundle.work_title.lower()
        ),
        None,
    )
    evidence_class = "direct_text"
    if bundle.evidence_role == "counter_evidence":
        evidence_class = "counter_evidence"
    elif school_hints and not school_match and not author_match:
        evidence_class = "ancient_testimony"

    period = str(
        profile.get("period") or bundle.metadata.get("author_period") or ""
    ).lower()
    late_penalty = 0
    if evidence_class == "ancient_testimony" and any(
        hint in period
        for hint in ("late", "imperial", "medieval", "byzantine", "christian")
    ):
        late_penalty = 8

    facet_overlap = 0
    for facet in state.research_notebook.facets:
        facet_terms = _tokenize_terms(
            " ".join([facet.title, facet.question, *facet.keywords])
        )
        if not facet_terms:
            continue
        haystack = " ".join(
            part
            for part in (
                bundle.author,
                bundle.work_title,
                bundle.section_path,
                bundle.canonical_ref,
                bundle.original_text,
                bundle.translation_text or "",
            )
            if part
        ).lower()
        facet_overlap = max(
            facet_overlap, sum(1 for term in facet_terms if term in haystack)
        )

    return {
        "author_match": author_match,
        "school_match": school_match,
        "work_priority_rank": work_priority_rank,
        "evidence_class": evidence_class,
        "late_penalty": late_penalty,
        "facet_overlap": facet_overlap,
        "author_period": profile.get("period"),
        "author_school": profile.get("school"),
        "author_role": profile.get("role"),
        "author_node_id": profile.get("node_id"),
    }


def _facet_bundle_score(
    bundle: EvidenceBundle, facet: ResearchFacet, state: RAGState
) -> int:
    facet_terms = _tokenize_terms(
        " ".join([facet.title, facet.question, *facet.keywords])
    )
    if not facet_terms:
        return _bundle_query_score(bundle, state)
    haystack = " ".join(
        part
        for part in (
            bundle.author,
            bundle.work_title,
            bundle.section_path,
            bundle.canonical_ref,
            truncate_text(bundle.original_text, 1600),
            truncate_text(bundle.translation_text, 1600)
            if bundle.translation_text
            else "",
        )
        if part
    ).lower()
    overlap = sum(1 for term in facet_terms if term in haystack)
    features = _bundle_academic_features(bundle, state)
    evidence_bonus = {
        "direct_text": 18,
        "ancient_testimony": 10,
        "counter_evidence": 6,
    }.get(features["evidence_class"], 4)
    if (
        facet.title.lower().startswith("counterpoint")
        or "nuance" in facet.title.lower()
    ):
        evidence_bonus = (
            16 if features["evidence_class"] == "counter_evidence" else evidence_bonus
        )
    return overlap * 18 + evidence_bonus + _bundle_query_score(bundle, state)


def _facet_node_score(ev: Evidence, facet: ResearchFacet, state: RAGState) -> int:
    facet_terms = _tokenize_terms(
        " ".join([facet.title, facet.question, *facet.keywords])
    )
    if not facet_terms:
        return _node_query_score(ev, state)
    haystack = " ".join(
        part
        for part in (ev.label, ev.type, ev.description, ev.period, ev.school, ev.role)
        if part
    ).lower()
    return sum(1 for term in facet_terms if term in haystack) * 14 + _node_query_score(
        ev, state
    )


def _bundle_label_from_id(state: RAGState, bundle_id: str) -> str:
    for bundle in state.evidence_bundles:
        if bundle.bundle_id == bundle_id:
            return _bundle_label(bundle)
    return bundle_id


def _bundle_quote_excerpt(
    bundle: EvidenceBundle, *, prefer_translation: bool = False, limit: int = 220
) -> str | None:
    text = (
        bundle.translation_text
        if prefer_translation and bundle.translation_text
        else bundle.original_text or bundle.translation_text
    )
    if not text:
        return None
    return truncate_text(text, limit)


def _diversify_bundles(
    bundles: list[EvidenceBundle], *, max_per_work: int
) -> list[EvidenceBundle]:
    """Front-load breadth across works before allowing one work to dominate."""
    prioritized: list[EvidenceBundle] = []
    overflow: list[EvidenceBundle] = []
    work_counts: dict[str, int] = {}
    for bundle in bundles:
        work_key = bundle.work_id or bundle.work_title.lower()
        count = work_counts.get(work_key, 0)
        if count < max_per_work:
            prioritized.append(bundle)
            work_counts[work_key] = count + 1
        else:
            overflow.append(bundle)
    return prioritized + overflow


def _build_scholarly_dossier(state: RAGState) -> ScholarlyDossier:
    notebook = _ensure_notebook(state)
    facets = notebook.facets or _default_research_facets(state)
    notebook.facets = _normalize_notebook_facets(state, facets)

    bundles = sorted(
        state.evidence_bundles,
        key=lambda bundle: _bundle_score(bundle, state),
        reverse=True,
    )
    nodes = sorted(
        [item for item in state.all_evidence() if item.type != "passage"],
        key=lambda item: _node_query_score(item, state),
        reverse=True,
    )

    dossier_facets: list[DossierFacet] = []
    primary_bundle_ids: list[str] = []
    testimony_bundle_ids: list[str] = []
    counter_bundle_ids: list[str] = []
    metadata_ids: list[str] = []

    for facet in notebook.facets:
        ranked_bundles = sorted(
            bundles,
            key=lambda bundle: _facet_bundle_score(bundle, facet, state),
            reverse=True,
        )
        ranked_bundles = _diversify_bundles(ranked_bundles, max_per_work=1)
        primary_ids_for_facet: list[str] = []
        testimony_ids_for_facet: list[str] = []
        counter_ids_for_facet: list[str] = []
        for bundle in ranked_bundles:
            score = _facet_bundle_score(bundle, facet, state)
            if score <= 0:
                continue
            evidence_class = _bundle_academic_features(bundle, state)["evidence_class"]
            if evidence_class == "counter_evidence":
                if len(counter_ids_for_facet) < 2:
                    counter_ids_for_facet.append(bundle.bundle_id)
                continue
            if evidence_class == "ancient_testimony":
                if len(testimony_ids_for_facet) < 2:
                    testimony_ids_for_facet.append(bundle.bundle_id)
                continue
            if len(primary_ids_for_facet) < 3:
                primary_ids_for_facet.append(bundle.bundle_id)

        ranked_nodes = sorted(
            nodes,
            key=lambda ev: _facet_node_score(ev, facet, state),
            reverse=True,
        )
        metadata_ids_for_facet = [
            ev.id for ev in ranked_nodes[:3] if _facet_node_score(ev, facet, state) > 0
        ][:2]

        primary_bundle_ids.extend(primary_ids_for_facet)
        testimony_bundle_ids.extend(testimony_ids_for_facet)
        counter_bundle_ids.extend(counter_ids_for_facet)
        metadata_ids.extend(metadata_ids_for_facet)

        primary_labels = [
            _bundle_label_from_id(state, bundle_id)
            for bundle_id in primary_ids_for_facet[:2]
        ]
        testimony_labels = [
            _bundle_label_from_id(state, bundle_id)
            for bundle_id in testimony_ids_for_facet[:2]
        ]
        counter_labels = [
            _bundle_label_from_id(state, bundle_id)
            for bundle_id in counter_ids_for_facet[:1]
        ]
        support_labels = [
            *primary_labels,
            *testimony_labels[:1],
        ]
        summary = ""
        if primary_labels:
            summary = (
                f"Direct textual evidence centers on {', '.join(primary_labels[:2])}."
            )
            if testimony_labels:
                summary += f" Ancient testimony is preserved by {', '.join(testimony_labels[:2])}."
        elif testimony_labels:
            summary = f"Surviving evidence is chiefly indirect, preserved by {', '.join(testimony_labels[:2])}."
        elif support_labels:
            summary = f"Best evidence comes from {', '.join(support_labels[:3])}."
        if counter_labels:
            summary += f" A significant counterpoint appears in {', '.join(counter_labels[:1])}."
        dossier_facets.append(
            DossierFacet(
                facet_id=facet.facet_id,
                title=facet.title,
                question=facet.question,
                summary=summary,
                primary_bundle_ids=primary_ids_for_facet,
                testimony_bundle_ids=testimony_ids_for_facet,
                counter_bundle_ids=counter_ids_for_facet,
                metadata_ids=metadata_ids_for_facet,
                note_ids=[
                    note.note_id
                    for note in notebook.reading_notes
                    if set(note.evidence_ids)
                    & set(
                        primary_ids_for_facet
                        + testimony_ids_for_facet
                        + counter_ids_for_facet
                    )
                ][:4],
                uncertainties=notebook.uncertainties[:2],
            )
        )

    dossier = ScholarlyDossier(
        question_frame=notebook.question_frame or state.question,
        facets=dossier_facets,
        primary_bundle_ids=list(dict.fromkeys(primary_bundle_ids))[:10],
        testimony_bundle_ids=list(dict.fromkeys(testimony_bundle_ids))[:8],
        counter_bundle_ids=list(dict.fromkeys(counter_bundle_ids))[:6],
        metadata_ids=list(dict.fromkeys(metadata_ids))[:8],
        interpretive_notes=notebook.competing_hypotheses[:4],
        insufficiency_notes=notebook.uncertainties[:4],
    )
    state.scholarly_dossier = dossier
    _trace_stage(
        state,
        "scholarly_dossier",
        {
            "facet_count": len(dossier.facets),
            "primary_bundle_ids": dossier.primary_bundle_ids[:10],
            "testimony_bundle_ids": dossier.testimony_bundle_ids[:8],
            "counter_bundle_ids": dossier.counter_bundle_ids[:6],
            "metadata_ids": dossier.metadata_ids[:8],
        },
    )
    return dossier


def _scholarly_dossier_payload(state: RAGState) -> dict[str, Any]:
    dossier = (
        state.scholarly_dossier
        if state.scholarly_dossier.facets
        else _build_scholarly_dossier(state)
    )
    notebook = _ensure_notebook(state)
    bundle_lookup = {bundle.bundle_id: bundle for bundle in state.evidence_bundles}
    node_lookup = {ev.id: ev for ev in state.all_evidence() if ev.type != "passage"}
    note_lookup = {note.note_id: note for note in notebook.reading_notes}

    def _bundle_payload(bundle_id: str) -> dict[str, Any]:
        bundle = bundle_lookup[bundle_id]
        return {
            "evidence_id": bundle.bundle_id,
            "ref": state.context_pack.bundle_refs.get(bundle.bundle_id),
            "label": _bundle_label(bundle),
            "author": bundle.author,
            "work_title": bundle.work_title,
            "canonical_ref": bundle.canonical_ref,
            "section_path": bundle.section_path,
            "language": bundle.language,
            "evidence_class": _bundle_academic_features(bundle, state)[
                "evidence_class"
            ],
            "quote_original_excerpt": _bundle_quote_excerpt(bundle),
            "quote_translation_excerpt": _bundle_quote_excerpt(
                bundle, prefer_translation=True
            ),
            "translation_available": bool(bundle.translation_text),
        }

    def _node_payload(node_id: str) -> dict[str, Any]:
        ev = node_lookup[node_id]
        return {
            "evidence_id": ev.id,
            "ref": state.context_pack.node_refs.get(ev.id),
            "label": ev.label,
            "type": ev.type,
            "period": ev.period,
            "school": ev.school,
        }

    return {
        "question_frame": dossier.question_frame,
        "interpretive_notes": dossier.interpretive_notes,
        "insufficiency_notes": dossier.insufficiency_notes,
        "facets": [
            {
                "facet_id": facet.facet_id,
                "title": facet.title,
                "question": facet.question,
                "summary": facet.summary,
                "primary_evidence": [
                    _bundle_payload(bundle_id)
                    for bundle_id in facet.primary_bundle_ids
                    if bundle_id in bundle_lookup
                ],
                "testimony_evidence": [
                    _bundle_payload(bundle_id)
                    for bundle_id in facet.testimony_bundle_ids
                    if bundle_id in bundle_lookup
                ],
                "counter_evidence": [
                    _bundle_payload(bundle_id)
                    for bundle_id in facet.counter_bundle_ids
                    if bundle_id in bundle_lookup
                ],
                "metadata_evidence": [
                    _node_payload(node_id)
                    for node_id in facet.metadata_ids
                    if node_id in node_lookup
                ],
                "support_balance": {
                    "direct_text_count": len(facet.primary_bundle_ids),
                    "testimony_count": len(facet.testimony_bundle_ids),
                    "counter_count": len(facet.counter_bundle_ids),
                    "metadata_count": len(facet.metadata_ids),
                },
                "reading_notes": [
                    note_lookup[note_id].thesis
                    for note_id in facet.note_ids
                    if note_id in note_lookup
                ],
            }
            for facet in dossier.facets
        ],
    }


def _trace_bucket(state: RAGState) -> dict[str, Any]:
    return state.metadata.setdefault("debug_trace", {})


def _trace_stage(state: RAGState, stage: str, payload: dict[str, Any]) -> None:
    _trace_bucket(state)[stage] = payload


def _compact_trace_value(value: Any) -> Any:
    if isinstance(value, str):
        return truncate_text(value, 240)
    if isinstance(value, list):
        return [_compact_trace_value(item) for item in value[:6]]
    if isinstance(value, dict):
        return {
            str(key): _compact_trace_value(item)
            for key, item in list(value.items())[:8]
        }
    return value


def _stage_status(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "skipped"
    mode = str(payload.get("mode") or "").lower()
    if mode == "skipped":
        return "skipped"
    if payload.get("error") or mode == "fallback":
        return "degraded"
    return "complete"


def _stage_summary(
    stage_id: str, payload: dict[str, Any] | None, state: RAGState
) -> str:
    if stage_id == "classify_query":
        query_type = state.metadata.get("query_type") or getattr(
            state.query_type, "value", state.query_type
        )
        confidence = state.metadata.get("classification_confidence")
        mode = payload.get("mode") if payload else None
        conf_text = (
            f"{round(float(confidence) * 100)}% confidence"
            if isinstance(confidence, float | int)
            else "heuristic confidence"
        )
        if query_type:
            return f"{query_type} selected with {conf_text}" + (
                f" via {mode}" if mode else ""
            )
        return "Query classification unavailable."

    if stage_id == "expand_query":
        terms = state.expansion_terms
        philosophers = len(getattr(terms, "philosophers", []) or [])
        concepts = len(getattr(terms, "concepts", []) or [])
        schools = len(getattr(terms, "schools", []) or [])
        return (
            f"{philosophers} philosophers, {concepts} concepts, and {schools} schools "
            f"added around the query frame."
        )

    if not payload:
        return "Stage skipped for this query."

    if stage_id == "discover_corpus":
        return (
            f"{len(payload.get('seed_node_ids', []))} seed nodes, "
            f"{len(payload.get('passage_anchor_ids', []))} passage anchors, "
            f"{len(payload.get('linked_passages', []))} linked passages."
        )
    if stage_id == "research_notebook":
        return (
            f"{len(payload.get('facets', []))} facets, "
            f"{len(payload.get('competing_hypotheses', []))} hypotheses, "
            f"{len(payload.get('work_priorities', []))} priority works."
        )
    if stage_id == "reading_plan":
        return (
            f"{len(payload.get('planned_work_titles', []))} planned works, "
            f"{len(payload.get('planned_facet_ids', []))} prioritized facets."
        )
    if stage_id == "scholarly_dossier":
        return (
            f"{payload.get('facet_count', 0)} dossier facets, "
            f"{len(payload.get('primary_bundle_ids', []))} direct bundles, "
            f"{len(payload.get('testimony_bundle_ids', []))} testimonia."
        )
    if stage_id == "tree_navigation":
        return (
            f"{len(payload.get('candidate_work_titles', []))} candidate works, "
            f"{len(payload.get('selected_sections', []))} selected sections."
        )
    if stage_id == "evidence_bundles":
        return f"{payload.get('bundle_count', 0)} evidence bundles assembled for answering."
    if stage_id == "counter_evidence":
        return (
            f"{payload.get('selected_count', 0)} counter-evidence bundles "
            f"with rationale: {payload.get('rationale', 'none')}."
        )
    if stage_id == "context_pack":
        return (
            f"{payload.get('passage_bundle_count', 0)} bundles, "
            f"{payload.get('section_summary_count', 0)} section summaries, "
            f"~{payload.get('token_estimate', 0)} tokens."
        )
    if stage_id == "evidence_sufficiency":
        score = payload.get("score")
        sufficient = payload.get("sufficient")
        if isinstance(score, float | int):
            return f"Sufficiency {round(float(score) * 100)}% ({'sufficient' if sufficient else 'needs more evidence'})."
        return "Evidence sufficiency evaluated."
    if stage_id == "draft_claim_ledger":
        return f"{payload.get('claim_count', 0)} claims drafted via {payload.get('mode', 'unknown')} mode."
    if stage_id == "render_grounded_answer":
        return (
            f"Answer rendered via {payload.get('mode', 'unknown')}; "
            f"polish mode: {payload.get('polish_mode', 'skipped')}."
        )
    if stage_id == "scholarly_polish":
        return f"Scholarly polish finished via {payload.get('mode', 'unknown')} mode."
    if stage_id == "programmatic_verify":
        return f"{payload.get('citation_count', 0)} citations verified in the final answer."

    return "Stage completed."


def _stage_metrics(
    stage_id: str, payload: dict[str, Any] | None, state: RAGState
) -> list[dict[str, Any]]:
    if stage_id == "classify_query":
        metrics = [
            {
                "label": "Type",
                "value": state.metadata.get("query_type")
                or getattr(state.query_type, "value", state.query_type),
            },
            {"label": "Complexity", "value": state.complexity.value},
        ]
        confidence = state.metadata.get("classification_confidence")
        if isinstance(confidence, float | int):
            metrics.append(
                {"label": "Confidence", "value": f"{round(float(confidence) * 100)}%"}
            )
        if payload and payload.get("mode"):
            metrics.append({"label": "Mode", "value": payload["mode"]})
        return metrics

    if stage_id == "expand_query":
        terms = state.expansion_terms
        return [
            {
                "label": "Philosophers",
                "value": len(getattr(terms, "philosophers", []) or []),
            },
            {"label": "Concepts", "value": len(getattr(terms, "concepts", []) or [])},
            {"label": "Schools", "value": len(getattr(terms, "schools", []) or [])},
        ]

    if not payload:
        return []

    metric_pairs: list[tuple[str, Any]] = []
    if stage_id == "discover_corpus":
        metric_pairs = [
            ("Semantic hits", len(payload.get("semantic_hits", []))),
            ("Seeds", len(payload.get("seed_node_ids", []))),
            ("Anchors", len(payload.get("passage_anchor_ids", []))),
            ("Linked passages", len(payload.get("linked_passages", []))),
        ]
    elif stage_id == "research_notebook":
        metric_pairs = [
            ("Facets", len(payload.get("facets", []))),
            ("Hypotheses", len(payload.get("competing_hypotheses", []))),
            ("Sub-queries", len(payload.get("sub_queries", []))),
            ("Works", len(payload.get("work_priorities", []))),
        ]
    elif stage_id == "reading_plan":
        metric_pairs = [
            ("Works", len(payload.get("planned_work_titles", []))),
            ("Facets", len(payload.get("planned_facet_ids", []))),
            ("Mode", payload.get("mode", "unknown")),
        ]
    elif stage_id == "scholarly_dossier":
        metric_pairs = [
            ("Facets", payload.get("facet_count", 0)),
            ("Direct", len(payload.get("primary_bundle_ids", []))),
            ("Testimony", len(payload.get("testimony_bundle_ids", []))),
            ("Counter", len(payload.get("counter_bundle_ids", []))),
        ]
    elif stage_id == "tree_navigation":
        metric_pairs = [
            ("Candidates", len(payload.get("candidate_work_titles", []))),
            ("Sections", len(payload.get("selected_sections", []))),
        ]
    elif stage_id == "evidence_bundles":
        metric_pairs = [
            ("Bundles", payload.get("bundle_count", 0)),
            (
                "Translations",
                sum(
                    1
                    for item in payload.get("bundle_sample", [])
                    if item.get("translation_source")
                ),
            ),
        ]
    elif stage_id == "counter_evidence":
        metric_pairs = [
            ("Selected", payload.get("selected_count", 0)),
            ("Mode", payload.get("mode", "unknown")),
        ]
    elif stage_id == "context_pack":
        metric_pairs = [
            ("KG metadata", payload.get("kg_metadata_count", 0)),
            ("Sections", payload.get("section_summary_count", 0)),
            ("Bundles", payload.get("passage_bundle_count", 0)),
            ("Tokens", payload.get("token_estimate", 0)),
        ]
    elif stage_id == "evidence_sufficiency":
        score = payload.get("score")
        metric_pairs = [
            ("Bundles", payload.get("bundle_count", 0)),
            ("Works", payload.get("work_count", 0)),
            ("Facets", payload.get("covered_facets", 0)),
            (
                "Score",
                f"{round(float(score) * 100)}%"
                if isinstance(score, float | int)
                else score,
            ),
        ]
    elif stage_id == "draft_claim_ledger":
        metric_pairs = [
            ("Mode", payload.get("mode", "unknown")),
            ("Claims", payload.get("claim_count", 0)),
        ]
    elif stage_id == "render_grounded_answer":
        metric_pairs = [
            ("Mode", payload.get("mode", "unknown")),
            ("Polish", payload.get("polish_mode", "skipped")),
        ]
    elif stage_id == "scholarly_polish":
        metric_pairs = [("Mode", payload.get("mode", "unknown"))]
    elif stage_id == "programmatic_verify":
        metric_pairs = [("Citations", payload.get("citation_count", 0))]

    tool_count = sum(
        1 for item in state.research_notebook.tool_calls if item.stage_id == stage_id
    )
    decision_count = sum(
        1
        for item in state.research_notebook.reading_decisions
        if item.stage_id == stage_id
    )
    if tool_count:
        metric_pairs.append(("Tools", tool_count))
    if decision_count:
        metric_pairs.append(("Decisions", decision_count))

    return [
        {"label": label, "value": value}
        for label, value in metric_pairs
        if value not in (None, "", [])
    ]


def _build_research_graph_payload(state: RAGState) -> dict[str, Any]:
    trace = _trace_bucket(state)
    notebook = state.research_notebook
    dossier = (
        state.scholarly_dossier
        if state.scholarly_dossier.facets
        else _build_scholarly_dossier(state)
    )
    bundle_refs = state.context_pack.bundle_refs
    node_refs = state.context_pack.node_refs
    dossier_by_id = {facet.facet_id: facet for facet in dossier.facets}
    tool_calls = notebook.tool_calls
    reading_decisions = notebook.reading_decisions

    stages: list[dict[str, Any]] = []
    for stage_id, title in RESEARCH_STAGE_SEQUENCE:
        payload = trace.get(stage_id)
        stages.append(
            {
                "id": stage_id,
                "title": title,
                "status": _stage_status(payload),
                "summary": _stage_summary(stage_id, payload, state),
                "metrics": _stage_metrics(stage_id, payload, state),
                "details": _compact_trace_value(payload) if payload else None,
            }
        )

    facets: list[dict[str, Any]] = []
    for facet in notebook.facets:
        dossier_facet = dossier_by_id.get(facet.facet_id)
        facets.append(
            {
                "facet_id": facet.facet_id,
                "title": facet.title,
                "question": facet.question,
                "summary": dossier_facet.summary if dossier_facet else "",
                "required_support": facet.required_support,
                "priority": facet.priority,
                "primary_count": len(dossier_facet.primary_bundle_ids)
                if dossier_facet
                else 0,
                "testimony_count": len(dossier_facet.testimony_bundle_ids)
                if dossier_facet
                else 0,
                "counter_count": len(dossier_facet.counter_bundle_ids)
                if dossier_facet
                else 0,
                "metadata_count": len(dossier_facet.metadata_ids)
                if dossier_facet
                else 0,
                "note_count": len(dossier_facet.note_ids) if dossier_facet else 0,
                "uncertainty_count": len(dossier_facet.uncertainties)
                if dossier_facet
                else 0,
            }
        )

    work_map: dict[str, dict[str, Any]] = {}
    for section in state.metadata.get("selected_sections", []):
        work_id = str(section.get("work_id") or "unknown")
        work = work_map.setdefault(
            work_id,
            {
                "work_id": work_id,
                "title": section.get("work_title")
                or section.get("title")
                or "Unknown work",
                "author": section.get("author"),
                "bundle_count": 0,
                "section_count": 0,
                "primary_count": 0,
                "testimony_count": 0,
                "counter_count": 0,
                "has_translation": False,
                "languages": [],
                "canonical_refs": [],
                "sections": [],
            },
        )
        work["section_count"] += 1
        work["sections"].append(
            {
                "node_id": section.get("node_id"),
                "title": section.get("title"),
                "path": section.get("path"),
            }
        )

    for bundle in state.evidence_bundles:
        work = work_map.setdefault(
            bundle.work_id,
            {
                "work_id": bundle.work_id,
                "title": bundle.work_title or "Unknown work",
                "author": bundle.author,
                "bundle_count": 0,
                "section_count": 0,
                "primary_count": 0,
                "testimony_count": 0,
                "counter_count": 0,
                "has_translation": False,
                "languages": [],
                "canonical_refs": [],
                "sections": [],
            },
        )
        work["title"] = work["title"] or bundle.work_title or "Unknown work"
        work["author"] = work["author"] or bundle.author
        work["bundle_count"] += 1
        evidence_class = _bundle_academic_features(bundle, state)["evidence_class"]
        if evidence_class == "counter_evidence":
            work["counter_count"] += 1
        elif evidence_class == "ancient_testimony":
            work["testimony_count"] += 1
        else:
            work["primary_count"] += 1
        if bundle.translation_text:
            work["has_translation"] = True
        if bundle.language and bundle.language not in work["languages"]:
            work["languages"].append(bundle.language)
        if bundle.canonical_ref and bundle.canonical_ref not in work["canonical_refs"]:
            work["canonical_refs"].append(bundle.canonical_ref)

    works = sorted(
        (
            {
                **payload,
                "languages": payload["languages"][:4],
                "canonical_refs": payload["canonical_refs"][:6],
                "sections": payload["sections"][:6],
            }
            for payload in work_map.values()
        ),
        key=lambda item: (
            -int(item["bundle_count"]),
            -int(item["section_count"]),
            str(item["title"]).lower(),
        ),
    )[:16]

    claims: list[dict[str, Any]] = []
    for item in state.claim_ledger:
        refs = [
            bundle_refs[eid] if eid in bundle_refs else node_refs[eid]
            for eid in item.evidence_ids
            if eid in bundle_refs or eid in node_refs
        ]
        claims.append(
            {
                "claim": item.claim,
                "facet_id": item.facet_id,
                "evidence_class": item.evidence_class,
                "support_type": item.support_type,
                "confidence": round(float(item.confidence), 4),
                "status": item.status.value
                if hasattr(item.status, "value")
                else str(item.status),
                "evidence_ids": item.evidence_ids,
                "refs": refs,
                "quote_original": truncate_text(item.quote_original, 500)
                if item.quote_original
                else None,
                "quote_translation": truncate_text(item.quote_translation, 500)
                if item.quote_translation
                else None,
                "proof_chain": getattr(item, "proof_chain", None),
            }
        )

    return {
        "overview": {
            "query_type": state.metadata.get("query_type")
            or getattr(state.query_type, "value", state.query_type),
            "complexity": state.complexity.value,
            "grounding_policy": state.grounding_policy.value,
            "quality_badge": state.quality_badge,
            "pipeline_degraded": bool(state.metadata.get("pipeline_degraded")),
            "claim_ledger_mode": state.metadata.get("claim_ledger_mode", "unknown"),
            "render_answer_mode": state.metadata.get("render_answer_mode", "unknown"),
            "scholarly_polish_mode": state.metadata.get(
                "scholarly_polish_mode", "skipped"
            ),
            "seed_node_count": len(state.seed_node_ids),
            "context_node_count": len(state.context_node_ids),
            "bundle_count": len(state.evidence_bundles),
            "work_count": len({bundle.work_id for bundle in state.evidence_bundles}),
            "claim_count": len(state.claim_ledger),
            "citation_count": len(state.citations),
            "tool_call_count": len(tool_calls),
            "decision_count": len(reading_decisions),
        },
        "stages": stages,
        "facets": facets,
        "works": works,
        "claims": claims,
        "hypotheses": notebook.competing_hypotheses[:8],
        "open_questions": notebook.open_questions[:8],
        "counter_evidence": notebook.counter_evidence[:8],
        "uncertainties": notebook.uncertainties[:8],
        "tool_calls": [
            {
                "tool_call_id": item.tool_call_id,
                "tool_name": item.tool_name,
                "stage_id": item.stage_id,
                "status": item.status,
                "query": item.query,
                "rationale": item.rationale,
                "work_id": item.work_id,
                "work_title": item.work_title,
                "section_path": item.section_path,
                "selected_ids": item.selected_ids[:12],
                "detail_count": item.detail_count,
                "details": _compact_trace_value(item.details),
            }
            for item in tool_calls[-24:]
        ],
        "reading_decisions": [
            {
                "decision_id": item.decision_id,
                "stage_id": item.stage_id,
                "decision_type": item.decision_type,
                "title": item.title,
                "rationale": item.rationale,
                "facet_id": item.facet_id,
                "selected_ids": item.selected_ids[:12],
                "rejected_ids": item.rejected_ids[:12],
                "supporting_refs": item.supporting_refs[:12],
                "metadata": _compact_trace_value(item.metadata),
            }
            for item in reading_decisions[-24:]
        ],
    }


def _is_primary_node(node: dict[str, Any]) -> bool:
    """Check if a KG node belongs to the primary (ancient) layer."""
    if node.get("role") == "modern_scholar":
        return False
    return node.get("type") != "Modern_Interpretation"


def _compact_node_line(ev: Evidence) -> str:
    extras: list[str] = []
    if ev.period:
        extras.append(ev.period)
    if ev.school:
        extras.append(ev.school)
    if ev.role:
        extras.append(ev.role)
    desc = truncate_text(ev.description or ev.text_content or "", 240)
    body = " | ".join(part for part in [ev.label, ev.type, *extras, desc] if part)
    return body


def _node_query_score(ev: Evidence, state: RAGState) -> int:
    terms = _question_terms(state)
    if not terms:
        return int(ev.score * 100)
    haystack = " ".join(
        part
        for part in (
            ev.label,
            ev.type,
            ev.period,
            ev.school,
            ev.role,
            ev.description,
        )
        if part
    ).lower()
    overlap = sum(1 for term in terms if term in haystack)
    return overlap * 10 + int(ev.score * 100)


def _bundle_query_score(bundle: EvidenceBundle, state: RAGState) -> int:
    terms = _question_terms(state)
    haystack = " ".join(
        part
        for part in (
            bundle.author,
            bundle.work_title,
            bundle.section_path,
            bundle.canonical_ref,
            truncate_text(bundle.original_text, 1200),
            truncate_text(bundle.translation_text, 1200)
            if bundle.translation_text
            else "",
        )
        if part
    ).lower()
    overlap = sum(1 for term in terms if term in haystack)

    work_priority_bonus = 0
    for title in state.research_notebook.work_priorities[:12]:
        if title and title.lower() == bundle.work_title.lower():
            work_priority_bonus = 12
            break

    source_bonus = {
        EvidenceSource.TREE_REASONING: 10,
        EvidenceSource.PASSAGE_CITATION: 7,
        EvidenceSource.SEMANTIC_SEARCH: 5,
        EvidenceSource.GRAPH_TRAVERSAL: 2,
    }.get(bundle.source, 3)

    translation_bonus = 0
    if _question_requests_translation(state) and bundle.translation_text:
        translation_bonus += 16
    if _question_requests_original(state) and bundle.language in {"grc", "lat"}:
        translation_bonus += 10

    ref_bonus = 0
    for ref_number in _question_reference_numbers(state):
        if bundle.canonical_ref and re.search(
            rf"\b{re.escape(ref_number)}\b", bundle.canonical_ref
        ):
            ref_bonus += 50 if _question_requests_quote(state) else 25
        elif bundle.section_path and re.search(
            rf"\b{re.escape(ref_number)}\b", bundle.section_path
        ):
            ref_bonus += 20

    features = _bundle_academic_features(bundle, state)
    evidence_class_bonus = {
        "direct_text": 24,
        "ancient_testimony": 14,
        "counter_evidence": 6,
    }.get(features["evidence_class"], 10)
    author_bonus = 18 if features["author_match"] else 0
    school_bonus = 18 if features["school_match"] else 0
    facet_bonus = features["facet_overlap"] * 10
    work_rank_bonus = max(0, 14 - (features["work_priority_rank"] or 99))
    late_penalty = features["late_penalty"]

    return (
        overlap * 12
        + work_priority_bonus
        + source_bonus
        + translation_bonus
        + ref_bonus
        + evidence_class_bonus
        + author_bonus
        + school_bonus
        + facet_bonus
        + work_rank_bonus
        - late_penalty
    )


def _top_bundle_debug_entries(
    scored_bundles: list[tuple[tuple[float, float, float, float], EvidenceBundle]],
    refs: dict[str, str],
    state: RAGState,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for score_tuple, bundle in scored_bundles[:8]:
        features = _bundle_academic_features(bundle, state)
        entries.append(
            {
                "ref": refs.get(bundle.bundle_id),
                "bundle_id": bundle.bundle_id,
                "work_title": bundle.work_title,
                "author": bundle.author,
                "source": bundle.source.value,
                "score": score_tuple[0],
                "canonical_ref": bundle.canonical_ref,
                "section_path": bundle.section_path,
                "evidence_class": features["evidence_class"],
                "author_match": features["author_match"],
                "school_match": features["school_match"],
                "late_penalty": features["late_penalty"],
            }
        )
    return entries


def _build_context_from_evidence(evidence: list[Evidence]) -> str:
    """Build a compact context string from evidence items."""
    parts: list[str] = []
    node_idx = 0
    passage_idx = 0
    for ev in evidence:
        if ev.type == "passage":
            passage_idx += 1
            parts.append(
                f"[P{passage_idx}] {ev.label}\n"
                f"{truncate_text(ev.text_content or ev.description, 1200)}"
            )
        else:
            node_idx += 1
            parts.append(f"[{node_idx}] {_compact_node_line(ev)}")
    return "\n\n".join(parts)


def _build_hierarchical_context(state: RAGState) -> str:
    """Build the final packed context or fall back to evidence-only context."""
    if state.context_pack.prompt_context:
        return state.context_pack.prompt_context
    return _build_context_from_evidence(state.all_evidence())


def _default_query_type(question: str):
    q = question.lower()
    if any(token in q for token in ("who", "when was", "what school")):
        return QueryType.SPECIFIC_ENTITY
    if any(token in q for token in ("compare", "versus", "difference", "differ")):
        return QueryType.COMPARATIVE
    if any(token in q for token in ("evolve", "development", "from", "through")):
        return QueryType.MULTI_HOP
    if any(token in q for token in ("when", "chronology", "period", "later")):
        return QueryType.TEMPORAL
    return QueryType.GLOBAL_ABSTRACT


def _default_expansion(question: str) -> ExpansionTerms:
    q = question.lower()
    greek_terms: list[dict[str, str]] = []
    concepts: list[str] = []
    philosophers: list[str] = []
    schools: list[str] = []
    for trigger, data in _STATIC_GREEK_TERMS.items():
        if trigger in q:
            greek_terms.extend(data["greek_terms"])
            concepts.extend(data["concepts"])
    for name in ("Chrysippus", "Epictetus", "Seneca", "Marcus Aurelius", "Cicero"):
        if name.lower() in q:
            philosophers.append(name)
    if "stoic" in q or "stoics" in q or "stoicism" in q:
        schools.append("Stoicism")
        philosophers.extend(
            [
                "Chrysippus",
                "Epictetus",
                "Seneca",
                "Marcus Aurelius",
                "Cleanthes",
                "Zeno of Citium",
            ]
        )
    if "responsibility" in q or "freedom" in q or "moral" in q:
        concepts.extend(["responsibility", "assent", "prohairesis"])
        greek_terms.extend(
            [
                {
                    "greek": "ἐφ' ἡμῖν",
                    "transliteration": "eph' hemin",
                    "translation": "up to us",
                },
                {
                    "greek": "συγκατάθεσις",
                    "transliteration": "synkatathesis",
                    "translation": "assent",
                },
            ]
        )

    return ExpansionTerms(
        expanded_query=question,
        greek_terms=greek_terms[:5],
        philosophers=philosophers[:5],
        concepts=concepts[:5],
        schools=schools[:3],
    )


def _merge_expansion_terms(
    primary: ExpansionTerms, fallback: ExpansionTerms
) -> ExpansionTerms:
    def _merge_str_lists(*values: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for value_list in values:
            for item in value_list:
                norm = item.strip().lower()
                if not norm or norm in seen:
                    continue
                seen.add(norm)
                merged.append(item)
        return merged

    def _merge_model_lists(*values: list[Any], keys: tuple[str, ...]) -> list[Any]:
        merged: list[Any] = []
        seen: set[tuple[str, ...]] = set()
        for value_list in values:
            for item in value_list:
                if isinstance(item, dict):
                    key = tuple(
                        str(item.get(part, "")).strip().lower() for part in keys
                    )
                else:
                    key = tuple(
                        str(getattr(item, part, "")).strip().lower() for part in keys
                    )
                if not any(key):
                    continue
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
        return merged

    return ExpansionTerms(
        expanded_query=primary.expanded_query or fallback.expanded_query,
        greek_terms=_merge_model_lists(
            primary.greek_terms, fallback.greek_terms, keys=("greek", "transliteration")
        )[:8],
        latin_terms=_merge_model_lists(
            primary.latin_terms, fallback.latin_terms, keys=("latin",)
        )[:8],
        philosophers=_merge_str_lists(primary.philosophers, fallback.philosophers)[:8],
        concepts=_merge_str_lists(primary.concepts, fallback.concepts)[:8],
        schools=_merge_str_lists(primary.schools, fallback.schools)[:5],
        periods=_merge_str_lists(primary.periods, fallback.periods)[:5],
    )


def _search_queries(state: RAGState) -> list[str]:
    queries: list[str] = []
    if state.expanded_query:
        queries.append(state.expanded_query)
    queries.extend(state.sub_queries)
    if state.expansion_terms:
        queries.extend(getattr(state.expansion_terms, "philosophers", [])[:3])
        queries.extend(getattr(state.expansion_terms, "concepts", [])[:3])
        queries.extend(getattr(state.expansion_terms, "schools", [])[:2])
    queries.append(state.question)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in queries:
        if not item:
            continue
        norm = item.strip().lower()
        if not norm or norm in seen:
            continue
        deduped.append(item.strip())
        seen.add(norm)
    return deduped


def _should_minimize_llm_calls(state: RAGState) -> bool:
    return (
        state.query_type == QueryType.SPECIFIC_ENTITY
        or state.complexity == QueryComplexity.SIMPLE
    )


def _expand_graph(
    deps: Deps,
    seed_ids: list[str],
    depth: int = 2,
    max_nodes: int | None = None,
) -> set[str]:
    """Fallback BFS expansion (when WeightedTraversal is unavailable)."""
    visited = set(seed_ids)
    queue = deque([(nid, 0) for nid in seed_ids])

    while queue:
        if max_nodes is not None and len(visited) >= max_nodes:
            break
        node_id, level = queue.popleft()
        if level >= depth:
            continue
        for edge in deps.outgoing_edges.get(node_id, []):
            target = edge["target"]
            if target in deps.node_lookup and target not in visited:
                visited.add(target)
                queue.append((target, level + 1))
        for edge in deps.incoming_edges.get(node_id, []):
            source = edge["source"]
            if source in deps.node_lookup and source not in visited:
                visited.add(source)
                queue.append((source, level + 1))
    return visited


def _make_evidence_from_node(
    node_id: str,
    node: dict[str, Any],
    *,
    score: float = 0.0,
    source: EvidenceSource = EvidenceSource.SEMANTIC_SEARCH,
) -> Evidence:
    layer = EvidenceLayer.PRIMARY if _is_primary_node(node) else EvidenceLayer.SECONDARY
    metadata = node.get("metadata", {}) or {}
    node_type = str(node.get("type", ""))
    is_passage = node_type.lower() in {"passage", "quote"}
    # Integrity-flagged descriptions are not citable text: never pack them
    # into the dossier/context pack (the node itself stays traversable).
    integrity_flagged = bool(_node_integrity_status(node))
    description = "" if integrity_flagged else node.get("description", "")
    return Evidence(
        id=node_id,
        label=node.get("label", node_id),
        type=node_type,
        layer=layer,
        source=source,
        description=description,
        score=score,
        period=node.get("period"),
        school=node.get("school"),
        role=node.get("role"),
        metadata=metadata,
        passage_id=node_id if is_passage else None,
        canonical_ref=metadata.get("canonical_ref") if is_passage else None,
        author=metadata.get("author") if is_passage else None,
        work_id=(
            metadata.get("work_id")
            or metadata.get("work_canonical_id")
            or metadata.get("source_work")
            or "snapshot"
            if is_passage
            else None
        ),
        work_title=(
            metadata.get("work_title") or metadata.get("source_work")
            if is_passage
            else None
        ),
        text_content=(
            node.get("description") if is_passage and not integrity_flagged else None
        ),
        language=metadata.get("language") if is_passage else None,
    )


def _candidate_work_titles(state: RAGState) -> list[str]:
    scored_titles: dict[str, tuple[str, int]] = {}
    terms = _question_terms(state)
    author_hints = _question_author_hints(state)
    school_hints = _question_school_hints(state)

    def _overlap_score(*parts: str | None) -> int:
        haystack = " ".join(part for part in parts if part).lower()
        return sum(1 for term in terms if term in haystack)

    def _ingest(title: str | None, score: int) -> None:
        if not title:
            return
        cleaned = title.strip()
        norm = cleaned.lower()
        if not norm:
            return
        existing = scored_titles.get(norm)
        if existing is None or score > existing[1]:
            scored_titles[norm] = (cleaned, score)

    for ev in state.primary_evidence:
        title: str | None = None
        score = 0
        if ev.work_title:
            title = ev.work_title
            score += 8
            if ev.type == "passage":
                score -= 4
        elif ev.type.lower() == "work":
            title = ev.label
            score += 18

        if title:
            score += (
                _overlap_score(title, ev.author, ev.description, ev.text_content) * 12
            )
            if ev.author and any(hint in ev.author.lower() for hint in author_hints):
                score += 18
            if (
                ev.school
                and school_hints
                and any(hint in ev.school.lower() for hint in school_hints)
            ):
                score += 14
            elif school_hints and ev.author and ev.type == "passage":
                score -= 6
            score += int((ev.score or ev.confidence or 0.0) * 40)
            if ev.source == EvidenceSource.SEMANTIC_SEARCH:
                score += 10
            elif ev.source == EvidenceSource.PASSAGE_CITATION:
                score += 4
            elif ev.source == EvidenceSource.TREE_REASONING:
                score += 6
            _ingest(title, score)

    for title in state.research_notebook.work_priorities:
        score = 6 + _overlap_score(title) * 8
        _ingest(title, score)

    ordered = sorted(
        scored_titles.values(), key=lambda item: (-item[1], item[0].lower())
    )
    return [title for title, _ in ordered]


_PASSAGE_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


async def _fetch_passages_for_nodes(
    deps: Deps,
    node_ids: list[str],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch passages linked to nodes via passage_citations.

    Anchors that are raw database passage UUIDs (returned by SQLStrategy,
    not KG node ids) are resolved directly against ``passages`` so they
    survive into evidence bundles.
    """
    if not node_ids:
        return []
    if not db_is_connected(deps.db):
        return linked_passage_rows(deps, node_ids, limit=limit)

    role_cond = passage_role_condition("p")
    placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
    limit_clause = f"LIMIT {limit}" if limit is not None else ""

    uuid_ids = [str(nid) for nid in node_ids if _PASSAGE_UUID_RE.match(str(nid))]
    direct_clause = ""
    if uuid_ids:
        offset = len(node_ids)
        direct_ph = ", ".join(f"${offset + i + 1}" for i in range(len(uuid_ids)))
        direct_clause = f"""
            UNION
            SELECT
                p.passage_id,
                p.work_id::text AS work_id,
                p.text_content,
                p.canonical_ref,
                p.sequence_number,
                w.title,
                w.author,
                w.language,
                1.0::double precision AS confidence
            FROM {DB_SCHEMA}.passages p
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE p.passage_id::text IN ({direct_ph})
              AND {role_cond}
        """

    try:
        rows: list[dict[str, Any]] = await deps.db.fetch(
            f"""
            SELECT DISTINCT
                p.passage_id,
                p.work_id::text AS work_id,
                p.text_content,
                p.canonical_ref,
                p.sequence_number,
                w.title,
                w.author,
                w.language,
                pc.confidence
            FROM {DB_SCHEMA}.passage_citations pc
            JOIN {DB_SCHEMA}.passages p ON pc.passage_id = p.passage_id
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE pc.kg_node_id IN ({placeholders})
              AND {role_cond}
            {direct_clause}
            ORDER BY confidence DESC NULLS LAST, sequence_number
            {limit_clause}
            """,
            *node_ids,
            *uuid_ids,
        )
        return rows
    except Exception:
        logger.warning("DB passage lookup failed; using KG snapshot passages")
        return linked_passage_rows(deps, node_ids, limit=limit)


async def _fetch_translation_for_passage(
    deps: Deps,
    passage_id: str,
) -> dict[str, Any] | None:
    """Find an English translation passage linked through translation_of edges."""
    if not deps.outgoing_edges and not deps.incoming_edges:
        return None
    if not db_is_connected(deps.db):
        return translation_for_passage(deps, passage_id)

    try:
        rows = await deps.db.fetch(
            f"""
            SELECT kg_node_id
            FROM {DB_SCHEMA}.passage_citations
            WHERE passage_id = $1
            """,
            passage_id,
        )
    except Exception:
        return translation_for_passage(deps, passage_id)
    source_nodes = [str(row["kg_node_id"]) for row in rows]
    if not source_nodes:
        return None

    translation_node_ids: list[str] = []
    seen: set[str] = set()
    for node_id in source_nodes:
        for edge in deps.incoming_edges.get(node_id, []):
            if edge.get("relation") == "translation_of":
                source = str(edge["source"])
                if source not in seen:
                    translation_node_ids.append(source)
                    seen.add(source)
        for edge in deps.outgoing_edges.get(node_id, []):
            if edge.get("relation") == "translation_of":
                target = str(edge["target"])
                if target not in seen:
                    translation_node_ids.append(target)
                    seen.add(target)

    if not translation_node_ids:
        return None

    def _translation_priority(node_id: str) -> tuple[int, str]:
        node = deps.node_lookup.get(node_id, {})
        metadata = (
            node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
        )
        language = str(metadata.get("language") or node.get("language") or "").lower()
        label = str(node.get("label") or "").lower()
        score = 0
        if language in {"eng", "en"}:
            score += 3
        if node_id.endswith("_en"):
            score += 2
        if "english" in label:
            score += 1
        return (-score, node_id)

    translation_node_ids = sorted(translation_node_ids, key=_translation_priority)

    placeholders = ", ".join(f"${i + 1}" for i in range(len(translation_node_ids)))
    try:
        target_rows = await deps.db.fetch(
            f"""
            SELECT DISTINCT
                p.passage_id,
                p.work_id::text AS work_id,
                p.text_content,
                p.canonical_ref,
                p.sequence_number,
                w.title,
                w.author,
                w.language,
                pc.confidence
            FROM {DB_SCHEMA}.passage_citations pc
            JOIN {DB_SCHEMA}.passages p ON pc.passage_id = p.passage_id
            JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
            WHERE pc.kg_node_id IN ({placeholders})
            ORDER BY pc.confidence DESC, p.sequence_number
            LIMIT 1
            """,
            *translation_node_ids,
        )
    except Exception:
        return translation_for_passage(deps, passage_id)
    if target_rows:
        return target_rows[0]

    # Live graph translations currently exist as KG passage nodes even when they
    # do not have a corresponding passage_citation row. Fall back to the node
    # description so the answer can still cite the aligned translation text.
    for node_id in translation_node_ids:
        node = deps.node_lookup.get(node_id)
        if not node:
            continue
        text = node.get("description")
        if not text or _node_integrity_status(node):
            continue
        metadata = (
            node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
        )
        return {
            "passage_id": None,
            "kg_node_id": node_id,
            "text_content": text,
            "canonical_ref": metadata.get("canonical_ref"),
            "sequence_number": None,
            "title": metadata.get("work_title") or node.get("label"),
            "author": metadata.get("author"),
            "language": metadata.get("language") or node.get("language"),
            "confidence": None,
            "source": "kg_node_description",
        }

    return None


async def _batch_fetch_translations(
    deps: Deps,
    passage_ids: list[str],
) -> dict[str, dict[str, Any] | None]:
    """Batch-fetch translations for multiple passage IDs in minimal DB round-trips.

    Returns a mapping of passage_id -> translation dict (same shape as
    ``_fetch_translation_for_passage`` output) or ``None``.
    """
    if not passage_ids or (not deps.outgoing_edges and not deps.incoming_edges):
        return dict.fromkeys(passage_ids)
    if not db_is_connected(deps.db):
        return {pid: translation_for_passage(deps, pid) for pid in passage_ids}

    # --- Step 1: one query to get KG node IDs for ALL passages ---
    placeholders = ", ".join(f"${i + 1}" for i in range(len(passage_ids)))
    try:
        rows = await deps.db.fetch(
            f"""
            SELECT passage_id::text, kg_node_id
            FROM {DB_SCHEMA}.passage_citations
            WHERE passage_id IN ({placeholders})
            """,
            *passage_ids,
        )
    except Exception:
        return {pid: translation_for_passage(deps, pid) for pid in passage_ids}

    # Build passage_id -> list[kg_node_id]
    passage_to_kg: dict[str, list[str]] = {}
    for row in rows:
        pid = str(row["passage_id"])
        passage_to_kg.setdefault(pid, []).append(str(row["kg_node_id"]))

    # --- Step 2: in-memory edge traversal (no DB needed) ---
    def _translation_priority(node_id: str) -> tuple[int, str]:
        node = deps.node_lookup.get(node_id, {})
        metadata = (
            node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
        )
        language = str(metadata.get("language") or node.get("language") or "").lower()
        label = str(node.get("label") or "").lower()
        score = 0
        if language in {"eng", "en"}:
            score += 3
        if node_id.endswith("_en"):
            score += 2
        if "english" in label:
            score += 1
        return (-score, node_id)

    # passage_id -> sorted list of translation node IDs
    passage_translation_nodes: dict[str, list[str]] = {}
    all_translation_node_ids: set[str] = set()
    for pid in passage_ids:
        source_nodes = passage_to_kg.get(pid, [])
        if not source_nodes:
            continue
        seen: set[str] = set()
        trans_ids: list[str] = []
        for node_id in source_nodes:
            for edge in deps.incoming_edges.get(node_id, []):
                if edge.get("relation") == "translation_of":
                    source = str(edge["source"])
                    if source not in seen:
                        trans_ids.append(source)
                        seen.add(source)
            for edge in deps.outgoing_edges.get(node_id, []):
                if edge.get("relation") == "translation_of":
                    target = str(edge["target"])
                    if target not in seen:
                        trans_ids.append(target)
                        seen.add(target)
        if trans_ids:
            trans_ids = sorted(trans_ids, key=_translation_priority)
            passage_translation_nodes[pid] = trans_ids
            all_translation_node_ids.update(trans_ids)

    # --- Step 3: one query for ALL translation passages ---
    translation_passages: dict[str, list[dict[str, Any]]] = {}
    if all_translation_node_ids:
        t_placeholders = ", ".join(
            f"${i + 1}" for i in range(len(all_translation_node_ids))
        )
        t_node_list = list(all_translation_node_ids)
        try:
            t_rows = await deps.db.fetch(
                f"""
                SELECT DISTINCT
                    pc.kg_node_id::text AS kg_node_id,
                    p.passage_id,
                    p.work_id::text AS work_id,
                    p.text_content,
                    p.canonical_ref,
                    p.sequence_number,
                    w.title,
                    w.author,
                    w.language,
                    pc.confidence
                FROM {DB_SCHEMA}.passage_citations pc
                JOIN {DB_SCHEMA}.passages p ON pc.passage_id = p.passage_id
                JOIN {DB_SCHEMA}.ancient_works w ON p.work_id = w.work_id
                WHERE pc.kg_node_id IN ({t_placeholders})
                ORDER BY pc.confidence DESC, p.sequence_number
                """,
                *t_node_list,
            )
        except Exception:
            return {pid: translation_for_passage(deps, pid) for pid in passage_ids}
        for t_row in t_rows:
            nid = str(t_row["kg_node_id"])
            translation_passages.setdefault(nid, []).append(t_row)

    # --- Step 4: assemble results per passage_id ---
    results: dict[str, dict[str, Any] | None] = {}
    for pid in passage_ids:
        trans_ids = passage_translation_nodes.get(pid)
        if not trans_ids:
            results[pid] = None
            continue

        # Try DB-backed translation first (pick best by priority order)
        found = False
        for t_node_id in trans_ids:
            t_rows_for_node = translation_passages.get(t_node_id)
            if t_rows_for_node:
                results[pid] = t_rows_for_node[0]
                found = True
                break
        if found:
            continue

        # Fallback: KG node description
        fallback = None
        for t_node_id in trans_ids:
            node = deps.node_lookup.get(t_node_id)
            if not node:
                continue
            text = node.get("description")
            if not text or _node_integrity_status(node):
                continue
            metadata = (
                node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
            )
            fallback = {
                "passage_id": None,
                "kg_node_id": t_node_id,
                "text_content": text,
                "canonical_ref": metadata.get("canonical_ref"),
                "sequence_number": None,
                "title": metadata.get("work_title") or node.get("label"),
                "author": metadata.get("author"),
                "language": metadata.get("language") or node.get("language"),
                "confidence": None,
                "source": "kg_node_description",
            }
            break
        results[pid] = fallback

    return results


def _bundle_from_passage_evidence(ev: Evidence) -> EvidenceBundle:
    original_text = ev.text_content or ev.description or ""
    return EvidenceBundle(
        bundle_id=f"{ev.work_id or 'unknown'}::{ev.passage_id or ev.id}",
        work_id=ev.work_id or "unknown",
        work_title=ev.work_title or "Unknown work",
        author=ev.author,
        section_path=ev.canonical_ref or "retrieved passage",
        canonical_ref=ev.canonical_ref,
        original_passage_id=ev.passage_id or ev.id,
        original_text=original_text,
        language=ev.language,
        token_estimate=RetrievalBudget.estimate_tokens(original_text),
        evidence_role="primary_support",
        source=ev.source,
        metadata={
            "sequence_number": ev.metadata.get("sequence_number")
            if isinstance(ev.metadata, dict)
            else None,
            "retrieval_confidence": ev.confidence,
        },
    )


async def _supplemental_passage_bundles(
    ctx: GraphRunContext[RAGState, Deps],
    existing_bundles: list[EvidenceBundle],
    seen_bundle_ids: set[str],
) -> list[EvidenceBundle]:
    state = ctx.state
    budget_limit = state.retrieval_budget.passage_bundle_limit()
    remaining = max(0, budget_limit - len(existing_bundles))
    if remaining <= 0:
        return []

    candidates = [
        _bundle_from_passage_evidence(ev)
        for ev in state.primary_evidence
        if (
            ev.type == "passage"
            and ev.passage_id
            and ev.work_id
            and (ev.text_content or ev.description)
        )
    ]
    candidates = [
        bundle for bundle in candidates if bundle.bundle_id not in seen_bundle_ids
    ]
    if not candidates:
        return []

    candidates.sort(key=lambda bundle: _bundle_score(bundle, state), reverse=True)
    target = min(remaining, max(4, min(16, budget_limit // 2)))
    selected = candidates[:target]
    for bundle in selected:
        if bundle.language in {"grc", "lat"}:
            translation = await _fetch_translation_for_passage(
                ctx.deps, bundle.original_passage_id
            )
            if translation and translation.get("text_content"):
                bundle.translation_text = translation.get("text_content")
                bundle.translation_passage_id = (
                    str(translation["passage_id"])
                    if translation.get("passage_id")
                    else None
                )
                bundle.token_estimate = RetrievalBudget.estimate_tokens(
                    "\n".join(
                        part
                        for part in (bundle.original_text, bundle.translation_text)
                        if part
                    )
                )
                bundle.metadata["translation_available"] = True
                bundle.metadata["translation_source"] = translation.get("source")
                bundle.metadata["translation_node_id"] = translation.get("kg_node_id")
        seen_bundle_ids.add(bundle.bundle_id)
    return selected


def _section_line(section: dict[str, Any]) -> str:
    title = section.get("title") or section["node_id"]
    path = section.get("path") or title
    abstract = section.get("abstract") or section.get("summary") or ""
    refs = section.get("canonical_refs") or []
    ref_part = f" [{', '.join(refs[:2])}]" if refs else ""
    return f"{path}{ref_part} | {truncate_text(abstract, 220)}"


def _bundle_label(bundle: EvidenceBundle) -> str:
    ref = f" {bundle.canonical_ref}" if bundle.canonical_ref else ""
    return f"{bundle.author or 'Unknown'}, {bundle.work_title}{ref}"


def _bundle_prompt_dict(bundle: EvidenceBundle, ref: str) -> dict[str, Any]:
    return {
        "ref": ref,
        "bundle_id": bundle.bundle_id,
        "label": _bundle_label(bundle),
        "section_path": bundle.section_path,
        "original_text": truncate_text(bundle.original_text, 500),
        "translation_text": truncate_text(bundle.translation_text, 500),
        "evidence_role": bundle.evidence_role,
    }


def _claim_ledger_catalog(state: RAGState) -> dict[str, Any]:
    """Compact evidence catalog used to keep claim-ledger IDs stable."""
    pack = state.context_pack
    non_passage = {
        item.id: item for item in state.all_evidence() if item.type != "passage"
    }
    bundle_entries = [
        {
            "ref": pack.bundle_refs.get(bundle.bundle_id, bundle.bundle_id),
            "evidence_id": bundle.bundle_id,
            "label": _bundle_label(bundle),
            "canonical_ref": bundle.canonical_ref,
            "section_path": bundle.section_path,
            "support_type": "passage",
        }
        for bundle in pack.passage_bundles
    ]
    node_entries = []
    for node_id, ref in pack.node_refs.items():
        evidence = non_passage.get(node_id)
        node_entries.append(
            {
                "ref": ref,
                "evidence_id": node_id,
                "label": evidence.label if evidence else node_id,
                "type": evidence.type if evidence else "metadata",
                "support_type": "metadata",
            }
        )
    return {
        "passage_bundles": bundle_entries,
        "kg_metadata": node_entries,
    }


def _normalize_claim_support_type(value: str) -> str:
    return "metadata" if value == "metadata" else "passage"


def _normalize_evidence_token(raw: str) -> str:
    token = raw.strip().strip("[](){}<>").strip().strip(".,;:")
    if token.lower().startswith("ref "):
        token = token[4:].strip()
    if token.lower().startswith("evidence_id:"):
        token = token.split(":", 1)[1].strip()
    if token.lower().startswith("bundle_id:"):
        token = token.split(":", 1)[1].strip()
    if token.lower().startswith("node_id:"):
        token = token.split(":", 1)[1].strip()
    if token.lower().startswith("json"):
        token = token[4:].strip()
    if token.lower().startswith("p") and token[1:].isdigit():
        return f"P{token[1:]}"
    return token


def _evidence_id_terms(raw_id: str) -> set[str]:
    terms: set[str] = set()
    for part in re.split(r"[^a-z0-9]+", raw_id.lower()):
        part = part.strip()
        if len(part) < 3:
            continue
        if re.fullmatch(r"[a-z]\d+[a-z]\d+[a-z]\d+[a-z]\d+", part):
            continue
        if re.fullmatch(r"[a-f0-9]{8,}", part):
            continue
        if part.endswith("s") and len(part) > 4:
            terms.add(part[:-1])
        terms.add(part)
    return terms


def _fuzzy_resolve_evidence_id(
    token: str,
    *,
    candidates: dict[str, str],
) -> str | None:
    token_terms = _evidence_id_terms(token)
    if not token_terms:
        return None

    best_match: str | None = None
    best_score = 0.0
    for candidate_token, evidence_id in candidates.items():
        candidate_terms = _evidence_id_terms(candidate_token)
        if not candidate_terms:
            continue
        overlap = token_terms & candidate_terms
        if len(overlap) < 2:
            continue
        score = len(overlap) / max(1, len(token_terms | candidate_terms))
        if score > best_score:
            best_score = score
            best_match = evidence_id

    if best_score >= 0.5:
        return best_match
    return None


def _resolve_claim_evidence_ids(
    evidence_ids: list[str],
    support_type: str,
    state: RAGState,
) -> list[str]:
    """Accept exact IDs, refs, and common ref-shaped aliases from the LLM."""
    pack = state.context_pack
    valid_ids = set(pack.bundle_refs) | set(pack.node_refs)
    if not evidence_ids:
        return []

    bundle_aliases: dict[str, str] = {}
    node_aliases: dict[str, str] = {}
    bundle_numeric_aliases: dict[str, str] = {}
    for bundle_id, ref in pack.bundle_refs.items():
        aliases = {
            bundle_id,
            ref,
            ref.lower(),
            f"[{ref}]",
            f"[{ref.lower()}]",
        }
        if ref.startswith("P") and ref[1:].isdigit():
            bundle_numeric_aliases[ref[1:]] = bundle_id
            aliases.update({ref[1:], f"[{ref[1:]}]"})
        for alias in aliases:
            bundle_aliases[alias] = bundle_id
    for node_id, ref in pack.node_refs.items():
        aliases = {
            node_id,
            ref,
            ref.lower(),
            f"[{ref}]",
            f"[{ref.lower()}]",
        }
        for alias in aliases:
            node_aliases[alias] = node_id

    resolved: list[str] = []
    preferred_support = _normalize_claim_support_type(support_type)
    for raw_id in evidence_ids:
        token = _normalize_evidence_token(str(raw_id))
        if not token:
            continue
        if token in valid_ids:
            resolved.append(token)
            continue
        if preferred_support == "passage" and token in bundle_aliases:
            resolved.append(bundle_aliases[token])
            continue
        if preferred_support == "metadata" and token in node_aliases:
            resolved.append(node_aliases[token])
            continue
        if token in bundle_numeric_aliases and preferred_support != "metadata":
            resolved.append(bundle_numeric_aliases[token])
            continue
        if token in bundle_aliases:
            resolved.append(bundle_aliases[token])
            continue
        if token in node_aliases:
            resolved.append(node_aliases[token])
            continue
        fuzzy_candidates = (
            node_aliases if preferred_support == "metadata" else bundle_aliases
        )
        fuzzy_match = _fuzzy_resolve_evidence_id(token, candidates=fuzzy_candidates)
        if not fuzzy_match and preferred_support == "passage":
            fuzzy_match = _fuzzy_resolve_evidence_id(token, candidates=node_aliases)
        if fuzzy_match:
            resolved.append(fuzzy_match)

    deduped: list[str] = []
    seen: set[str] = set()
    for evidence_id in resolved:
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        deduped.append(evidence_id)
    return deduped


def _bundle_score(
    bundle: EvidenceBundle, state: RAGState
) -> tuple[float, float, float, float]:
    query_score = _bundle_query_score(bundle, state)
    features = _bundle_academic_features(bundle, state)
    source_weight = 2 if bundle.source == EvidenceSource.TREE_REASONING else 1
    evidence_weight = {
        "direct_text": 3,
        "ancient_testimony": 2,
        "counter_evidence": 1,
    }.get(features["evidence_class"], 1)
    # Optional cross-encoder rerank score (set by the reranker pass when
    # ELEUTHERIA_RERANKER is enabled). Acts as a tie-break after the
    # query score so the query_score>0 packing filter keeps its semantics;
    # 0.0 (absent) reproduces the legacy ordering exactly.
    rerank_raw = bundle.metadata.get("rerank_score")
    try:
        rerank_score = float(rerank_raw) if rerank_raw is not None else 0.0
    except (TypeError, ValueError):  # fmt: skip
        rerank_score = 0.0
    return (
        float(query_score),
        rerank_score,
        float(evidence_weight + source_weight),
        float(-bundle.token_estimate),
    )


def _format_token_budget(value: int) -> str:
    """Compact token count for log lines: 120000 -> '120k', 1000000 -> '1M'."""
    if value >= 1_000_000 and value % 1_000_000 == 0:
        return f"{value // 1_000_000}M"
    if value >= 1000:
        return f"{value // 1000}k"
    return str(value)


def _synthesis_budget_for_state(state: RAGState) -> RetrievalBudget:
    """Size the synthesis pack budget by the planner's complexity tier.

    ``ELEUTHERIA_SYNTH_CONTEXT_TOKENS`` stays the ceiling; a quick/standard
    query packs against a smaller per-tier cap so a simple question does not
    hand the synthesis model a ceiling-sized prompt. Deep (survey-of-debates,
    transmission-trace) and the legacy plan-less paths keep the full ceiling.
    """
    budget = state.retrieval_budget
    tier = getattr(getattr(state, "research_plan", None), "budget_tier", None)
    scoped = budget.for_synthesis_tier(tier)
    logger.info(
        "synthesis context budget: %s (tier=%s, ceiling=%s)",
        _format_token_budget(scoped.model_window),
        tier or "none",
        _format_token_budget(budget.model_window),
    )
    return scoped


def _build_context_pack(state: RAGState) -> ContextPack:
    """Pack KG metadata, section summaries, and bundles into a long context."""
    budget = _synthesis_budget_for_state(state)
    pack = ContextPack()

    kg_budget = budget.layer_budget("kg_metadata")
    node_idx = 1
    for ev in sorted(
        [item for item in state.all_evidence() if item.type != "passage"],
        key=lambda item: _node_query_score(item, state),
        reverse=True,
    ):
        line = f"[{node_idx}] {_compact_node_line(ev)}"
        line_tokens = budget.estimate_tokens(line)
        if (
            sum(budget.estimate_tokens(item) for item in pack.kg_metadata) + line_tokens
            > kg_budget
        ):
            continue
        pack.kg_metadata.append(line)
        pack.node_refs[ev.id] = str(node_idx)
        node_idx += 1

    section_budget = budget.layer_budget("section_summaries")
    selected_sections = state.metadata.get("selected_sections", [])
    for section in selected_sections:
        line = _section_line(section)
        line_tokens = budget.estimate_tokens(line)
        if (
            sum(budget.estimate_tokens(item) for item in pack.section_summaries)
            + line_tokens
            > section_budget
        ):
            continue
        pack.section_summaries.append(line)

    passage_budget = budget.layer_budget("passage_bundles")
    bundle_idx = 1
    bundle_tokens_used = 0
    scored_bundles = sorted(
        [(_bundle_score(bundle, state), bundle) for bundle in state.evidence_bundles],
        key=lambda item: item[0],
        reverse=True,
    )
    if any(score_tuple[0] > 0 for score_tuple, _ in scored_bundles):
        scored_bundles = [item for item in scored_bundles if item[0][0] > 0]
    prioritized_pairs: list[
        tuple[tuple[float, float, float, float], EvidenceBundle]
    ] = []
    overflow_pairs: list[tuple[tuple[float, float, float, float], EvidenceBundle]] = []
    work_counts: dict[str, int] = {}
    for item in scored_bundles:
        bundle = item[1]
        work_key = bundle.work_id or bundle.work_title.lower()
        count = work_counts.get(work_key, 0)
        if count < 2:
            prioritized_pairs.append(item)
            work_counts[work_key] = count + 1
        else:
            overflow_pairs.append(item)
    scored_bundles = prioritized_pairs + overflow_pairs
    for _score_tuple, bundle in scored_bundles:
        if bundle_tokens_used + bundle.token_estimate > passage_budget:
            continue
        ref = f"P{bundle_idx}"
        pack.bundle_refs[bundle.bundle_id] = ref
        pack.passage_bundles.append(bundle)
        bundle_tokens_used += bundle.token_estimate
        bundle_idx += 1

    # Scholar-RAG M3: a top-level ``## Controversy Frames`` layer serialising the
    # assembled fault lines (positions w/ holder+page, ``A --opposes--> B`` link
    # lines, contested passages original+English). This gives the synthesis
    # prompt a first-class edge slot (failure-map F2 fix). Only emitted when the
    # flag is on AND a ControversyMap was assembled — inert by default so the
    # legacy three-layer pack is byte-for-byte unchanged.
    if scholar_rag_enabled() and state.controversy_map is not None:
        from eleutheria_graphrag.agents.controversy_map import (
            render_controversy_frames_layer,
        )

        pack.controversy_frames = list(state.controversy_map.frames)
        frames_layer = render_controversy_frames_layer(state.controversy_map)
    else:
        frames_layer = ""

    parts: list[str] = []
    if frames_layer:
        parts.append(frames_layer)
    if pack.kg_metadata:
        parts.append("## KG Metadata\n" + "\n".join(pack.kg_metadata))
    if pack.section_summaries:
        parts.append("## Work Sections\n" + "\n".join(pack.section_summaries))
    if pack.passage_bundles:
        bundle_lines = []
        for bundle in pack.passage_bundles:
            ref = pack.bundle_refs[bundle.bundle_id]
            # Full passage text by design (1M-token context): the per-layer
            # RetrievalBudget gate above already bounds total bundle tokens,
            # and quote-containment verification needs the uncut original.
            lines = [
                f"[{ref}] {_bundle_label(bundle)}",
                f"Section: {bundle.section_path or 'unknown'}",
                f'Original: "{bundle.original_text}"',
            ]
            if bundle.translation_text:
                lines.append(f'Translation: "{bundle.translation_text}"')
            bundle_lines.append("\n".join(lines))
        parts.append("## Evidence Bundles\n" + "\n\n".join(bundle_lines))

    pack.prompt_context = "\n\n".join(parts)
    pack.token_estimate = RetrievalBudget.estimate_tokens(pack.prompt_context)
    _trace_stage(
        state,
        "context_pack",
        {
            "kg_metadata_count": len(pack.kg_metadata),
            "section_summary_count": len(pack.section_summaries),
            "passage_bundle_count": len(pack.passage_bundles),
            "token_estimate": pack.token_estimate,
            "synthesis_budget_tokens": budget.model_window,
            "synthesis_budget_ceiling": state.retrieval_budget.model_window,
            "top_bundle_rankings": _top_bundle_debug_entries(
                scored_bundles, pack.bundle_refs, state
            ),
        },
    )
    return pack


def _reverse_ref_maps(
    state: RAGState,
) -> tuple[dict[str, EvidenceBundle], dict[str, Evidence]]:
    bundle_index = {b.bundle_id: b for b in state.context_pack.passage_bundles}
    bundles_by_ref = {
        ref: bundle_index[bundle_id]
        for bundle_id, ref in state.context_pack.bundle_refs.items()
        if bundle_id in bundle_index
    }
    node_index = {ev.id: ev for ev in state.all_evidence()}
    nodes_by_ref = {
        ref: node_index[node_id]
        for node_id, ref in state.context_pack.node_refs.items()
        if node_id in node_index
    }
    return bundles_by_ref, nodes_by_ref


def _claim_reference_refs(state: RAGState, item: ClaimLedgerItem) -> list[str]:
    """Return stable, de-duplicated refs with passage-first grounding semantics."""
    passage_refs: list[str] = []
    node_refs: list[str] = []
    for evidence_id in item.evidence_ids:
        bundle_ref = state.context_pack.bundle_refs.get(evidence_id)
        if bundle_ref:
            passage_refs.append(bundle_ref)
            continue
        node_ref = state.context_pack.node_refs.get(evidence_id)
        if node_ref:
            node_refs.append(node_ref)

    if item.support_type == "passage":
        ordered = passage_refs or node_refs
    elif item.support_type == "metadata":
        ordered = node_refs or passage_refs
    else:
        ordered = passage_refs + node_refs

    # Avoid cluttering passage-backed doctrinal claims with metadata refs.
    if item.support_type == "passage" and passage_refs:
        ordered = passage_refs
    elif item.support_type == "metadata" and node_refs:
        ordered = node_refs

    return list(dict.fromkeys(ordered))


def _claim_reference_markers(state: RAGState, item: ClaimLedgerItem) -> list[str]:
    return [f"[{ref}]" for ref in _claim_reference_refs(state, item)]


def _strip_section_prefix(claim: str, facet_title: str | None) -> str:
    """Remove a leading "Section Title: " prefix from a claim string.

    The structured-output claim ledger sometimes echoes the facet title at
    the start of each claim (``"Textual Witnesses: Bobzien argues..."``).
    When we then render the claim inside a section that already carries
    that title, the duplication produces ``"### Textual Witnesses\nTextual
    Witnesses: Bobzien argues..."``. This helper strips the prefix when
    it matches the facet title or any other obvious section label, so each
    section reads naturally.
    """
    if not claim:
        return claim
    text = claim.lstrip()
    candidates: list[str] = []
    if facet_title:
        candidates.append(facet_title)
    candidates.extend(
        [
            "Core Doctrinal Thesis",
            "Textual Witnesses",
            "Ancient Testimony",
            "Modern Reception",
            "Counterpoints and Limits",
            "Counter-Evidence",
            "Limits of the Evidence",
        ]
    )
    for candidate in candidates:
        if not candidate:
            continue
        prefix = f"{candidate}:"
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix) :].lstrip()
    return claim


def _render_answer_fallback(state: RAGState) -> str:
    """Deterministic fallback answer that is guaranteed to stay grounded.

    The renderer distributes claims across the dossier's facets so each
    required section receives a *distinct* claim where possible, rather
    than recycling the same lead claim under every header. When a facet
    has no claim of its own we emit a neutral note pointing readers to
    the limits section, instead of repeating earlier content.
    """
    lines: list[str] = []
    facets = (
        state.scholarly_dossier.facets[:4] if state.scholarly_dossier.facets else []
    )
    facet_titles = {facet.facet_id: facet.title for facet in facets}
    claims_by_facet: dict[str, list[ClaimLedgerItem]] = {}
    for item in state.claim_ledger:
        claims_by_facet.setdefault(item.facet_id or "_general", []).append(item)

    # Distribute "_general" claims across empty facets so each section is
    # filled with a *distinct* claim where possible. This prevents the
    # "every section restates claim 1" anti-pattern we saw in production
    # when the LLM emitted unfaceted claims.
    if facets:
        general_pool = list(claims_by_facet.get("_general", []))
        if general_pool:
            for facet in facets:
                if claims_by_facet.get(facet.facet_id):
                    continue
                if not general_pool:
                    break
                claims_by_facet.setdefault(facet.facet_id, []).append(
                    general_pool.pop(0)
                )
            # Leftover unfaceted claims roll into the first facet's overflow.
            if general_pool and facets:
                claims_by_facet.setdefault(facets[0].facet_id, []).extend(general_pool)
            claims_by_facet.pop("_general", None)

    used_claim_ids: set[int] = set()

    def _consume(facet_id: str) -> list[ClaimLedgerItem]:
        bucket = claims_by_facet.get(facet_id, [])
        fresh = [item for item in bucket if id(item) not in used_claim_ids]
        for item in fresh:
            used_claim_ids.add(id(item))
        return fresh

    supported_claims = [
        item
        for item in state.claim_ledger
        if item.status == ClaimStatus.SUPPORTED
        and _claim_reference_markers(state, item)
    ]
    # Emit the intro summary only when (a) there are no facets that would
    # carry the claim into a section, or (b) we are signalling insufficient
    # evidence. Otherwise the sections themselves carry the content and an
    # intro line would just duplicate the lead claim verbatim.
    intro_item: ClaimLedgerItem | None = None
    if supported_claims and (not facets or state.insufficient_evidence):
        intro_item = supported_claims[0]
        intro_refs = " ".join(_claim_reference_markers(state, intro_item))
        intro_line = _strip_section_prefix(intro_item.claim, None).rstrip(".")
        if state.insufficient_evidence:
            intro_line = f"Available evidence is partial, but the best-supported result is this: {intro_line}"
        lines.append(f"{intro_line}. {intro_refs}".replace("..", "."))

    empty_section_note = (
        "No direct evidence catalogued for this facet — see *Limits of the "
        "Evidence* for related material."
    )

    if facets:
        for facet in facets:
            facet_claims = _consume(facet.facet_id)
            # Fall back to the bucket if every claim was already consumed by
            # the intro — but ONLY if no other section has used it yet.
            if not facet_claims:
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(f"### {facet.title}")
                lines.append(empty_section_note)
                continue
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"### {facet.title}")
            prose_items = [item for item in facet_claims if item.claim]
            if prose_items:
                body_parts: list[str] = []
                for item in prose_items[:2]:
                    refs = _claim_reference_markers(state, item)
                    if not refs:
                        continue
                    claim_text = _strip_section_prefix(item.claim, facet.title)
                    body_parts.append(f"{claim_text.rstrip('.')} {' '.join(refs)}")
                if body_parts:
                    lines.append(" ".join(body_parts))
            quote_item = next(
                (
                    item
                    for item in facet_claims
                    if item.quote_original or item.quote_translation
                ),
                None,
            )
            if quote_item is not None:
                refs = _claim_reference_markers(state, quote_item)
                if refs:
                    if quote_item.quote_original:
                        lines.append(
                            f'> Original: "{quote_item.quote_original}" {" ".join(refs)}'
                        )
                    if quote_item.quote_translation:
                        lines.append(
                            f'> Translation: "{quote_item.quote_translation}" {" ".join(refs)}'
                        )
        if state.scholarly_dossier.insufficiency_notes:
            note_refs = (
                _claim_reference_markers(state, supported_claims[0])
                if supported_claims
                else []
            )
            if note_refs:
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append("### Limits of the Evidence")
                for note in state.scholarly_dossier.insufficiency_notes[:2]:
                    lines.append(f"{note.rstrip('.')} {' '.join(note_refs)}")
    else:
        for item in state.claim_ledger:
            refs = _claim_reference_markers(state, item)
            if not refs:
                continue
            claim_text = _strip_section_prefix(
                item.claim,
                facet_titles.get(item.facet_id or ""),
            )
            lines.append(f"{claim_text.rstrip('.')} {' '.join(refs)}")
            if item.quote_original:
                lines.append(f'> Original: "{item.quote_original}" {" ".join(refs)}')
            if item.quote_translation:
                lines.append(
                    f'> Translation: "{item.quote_translation}" {" ".join(refs)}'
                )

    if not lines and state.insufficient_evidence:
        return "Available evidence in the current corpus is insufficient to answer confidently."
    if not lines:
        for item in state.claim_ledger:
            refs = _claim_reference_markers(state, item)
            if not refs:
                continue
            claim_text = _strip_section_prefix(
                item.claim,
                facet_titles.get(item.facet_id or ""),
            )
            lines.append(f"{claim_text.rstrip('.')} {' '.join(refs)}")
    if not lines:
        return "Available evidence in the current corpus is insufficient to answer confidently."
    return "\n".join(lines)


def _update_insufficiency_flags_from_claims(state: RAGState) -> None:
    """Derive insufficiency from the final claim ledger for quote-style queries."""
    claims = state.claim_ledger
    if not claims:
        return

    all_insufficient = all(item.status == ClaimStatus.INSUFFICIENT for item in claims)
    supported_passage_claim = any(
        item.support_type == "passage"
        and item.status == ClaimStatus.SUPPORTED
        and item.evidence_ids
        for item in claims
    )
    quote_request = (
        _question_requests_quote(state)
        or _question_requests_original(state)
        or _question_requests_translation(state)
    )
    insufficient = (
        state.insufficient_evidence
        or all_insufficient
        or (quote_request and not supported_passage_claim)
    )
    state.insufficient_evidence = insufficient
    if insufficient:
        state.metadata["insufficient_evidence"] = True


def _render_evidence_packet(state: RAGState) -> list[dict[str, Any]]:
    """Compact selected evidence for the final prose pass."""
    packet: list[dict[str, Any]] = []
    seen: set[str] = set()
    evidence_by_id = {ev.id: ev for ev in state.all_evidence() if ev.type != "passage"}
    bundles_by_id = {
        bundle.bundle_id: bundle for bundle in state.context_pack.passage_bundles
    }

    dossier_order = [
        *state.scholarly_dossier.primary_bundle_ids,
        *state.scholarly_dossier.testimony_bundle_ids,
        *state.scholarly_dossier.counter_bundle_ids,
        *state.scholarly_dossier.metadata_ids,
    ]
    for evidence_id in dossier_order:
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        if evidence_id in bundles_by_id:
            bundle = bundles_by_id[evidence_id]
            packet.append(
                {
                    "evidence_id": evidence_id,
                    "ref": state.context_pack.bundle_refs.get(evidence_id),
                    "type": "passage",
                    "evidence_class": _bundle_academic_features(bundle, state)[
                        "evidence_class"
                    ],
                    "label": _bundle_label(bundle),
                    "canonical_ref": bundle.canonical_ref,
                    "section_path": bundle.section_path,
                    "original_text": truncate_text(bundle.original_text, 2000),
                    "translation_text": truncate_text(bundle.translation_text, 2000)
                    if bundle.translation_text
                    else None,
                }
            )
        elif evidence_id in evidence_by_id:
            ev = evidence_by_id[evidence_id]
            packet.append(
                {
                    "evidence_id": evidence_id,
                    "ref": state.context_pack.node_refs.get(evidence_id),
                    "type": "metadata",
                    "label": ev.label,
                    "description": truncate_text(
                        ev.description or ev.text_content or "", 420
                    ),
                    "period": ev.period,
                    "school": ev.school,
                }
            )

    for item in state.claim_ledger:
        for evidence_id in item.evidence_ids:
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            if evidence_id in bundles_by_id:
                bundle = bundles_by_id[evidence_id]
                packet.append(
                    {
                        "evidence_id": evidence_id,
                        "ref": state.context_pack.bundle_refs.get(evidence_id),
                        "type": "passage",
                        "evidence_class": item.evidence_class,
                        "label": _bundle_label(bundle),
                        "canonical_ref": bundle.canonical_ref,
                        "section_path": bundle.section_path,
                        "original_text": truncate_text(bundle.original_text, 900),
                        "translation_text": truncate_text(bundle.translation_text, 900)
                        if bundle.translation_text
                        else None,
                    }
                )
            elif evidence_id in evidence_by_id:
                ev = evidence_by_id[evidence_id]
                packet.append(
                    {
                        "evidence_id": evidence_id,
                        "ref": state.context_pack.node_refs.get(evidence_id),
                        "type": "metadata",
                        "label": ev.label,
                        "description": truncate_text(
                            ev.description or ev.text_content or "", 420
                        ),
                        "period": ev.period,
                        "school": ev.school,
                    }
                )
    return packet


def _select_direct_quote_bundle(state: RAGState) -> EvidenceBundle | None:
    """Pick the best exact bundle for philological quote requests."""
    if not (
        _question_requests_quote(state)
        or _question_requests_original(state)
        or _question_requests_translation(state)
    ):
        return None

    ref_numbers = _question_reference_numbers(state)
    terms = _question_terms(state)
    candidates: list[tuple[int, EvidenceBundle]] = []
    for bundle in state.context_pack.passage_bundles:
        score = 0
        if bundle.canonical_ref and any(
            re.search(rf"\b{re.escape(number)}\b", bundle.canonical_ref)
            for number in ref_numbers
        ):
            score += 100
        label_haystack = " ".join(
            part
            for part in (bundle.author, bundle.work_title, bundle.canonical_ref)
            if part
        ).lower()
        score += sum(10 for term in terms if term in label_haystack)
        if _question_requests_original(state) and bundle.original_text:
            score += 20
        if _question_requests_translation(state) and bundle.translation_text:
            score += 20
        if score > 0:
            candidates.append((score, bundle))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    best = candidates[0][1]
    if _question_requests_original(state) and not best.original_text:
        return None
    if _question_requests_translation(state) and not best.translation_text:
        return None
    return best


def _heuristic_claim_ledger_acceptable(
    state: RAGState, claims: list[ClaimLedgerItem]
) -> bool:
    """Treat the deterministic ledger as first-class when it covers the question well."""
    if _question_requests_quote(state):
        return False
    if len(claims) < 4:
        return False
    covered_facets = {
        item.facet_id
        for item in claims
        if item.facet_id and item.status == ClaimStatus.SUPPORTED and item.evidence_ids
    }
    has_metadata = any(
        item.support_type == "metadata" and item.evidence_ids for item in claims
    )
    has_passage = any(
        item.support_type == "passage" and item.evidence_ids for item in claims
    )
    if state.query_type == QueryType.SPECIFIC_ENTITY:
        return has_metadata and has_passage
    return has_passage and (
        has_metadata or len(covered_facets) >= 2 or len(claims) >= 6
    )


def _dedupe_claims(
    claims: list[ClaimLedgerItem], *, limit: int = 18
) -> list[ClaimLedgerItem]:
    deduped: list[ClaimLedgerItem] = []
    seen_signatures: set[tuple[str, tuple[str, ...]]] = set()
    for item in claims:
        signature = (item.claim, tuple(item.evidence_ids))
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _supported_dossier_facets(state: RAGState) -> list[DossierFacet]:
    dossier = (
        state.scholarly_dossier
        if state.scholarly_dossier.facets
        else _build_scholarly_dossier(state)
    )
    return [
        facet
        for facet in dossier.facets
        if facet.primary_bundle_ids or facet.testimony_bundle_ids or facet.metadata_ids
    ]


def _render_requirements(state: RAGState) -> dict[str, int]:
    """Compute the doctoral-grade rendering targets for ``state``.

    Targets calibrated for a published-thesis register: a 4-facet, 4-quote
    dossier should produce a ~10 k-char answer in 6+ sections; an 8-facet,
    6-quote dossier should produce ~15 k+ chars in 10 sections. The
    previous calibration (3 k–7 k chars, 4 sections) was producing
    journal-blog-length answers, not chapter sections.
    """
    supported_facets = _supported_dossier_facets(state)
    quoted_claims = sum(
        1
        for item in state.claim_ledger
        if item.quote_original or item.quote_translation
    )

    # Require enough sections for a chapter-style structure.
    required_sections = 0
    if len(supported_facets) >= 2:
        # Always add 2 framing sections (introduction + conclusion) on top
        # of the facet-driven body sections.
        required_sections = min(10, len(supported_facets) + 2)
    elif supported_facets:
        required_sections = 3

    # One quote block per substantive section, with a higher ceiling.
    required_quote_blocks = 0
    if quoted_claims:
        required_quote_blocks = min(8, max(4, quoted_claims))

    # Chapter-section-length floor.
    min_chars = 3000
    if supported_facets:
        min_chars += 1200 * min(8, len(supported_facets))
    if quoted_claims:
        min_chars += 600 * min(6, quoted_claims)
    if state.insufficient_evidence:
        min_chars = max(1800, min_chars - 1000)

    return {
        "required_sections": required_sections,
        "required_quote_blocks": required_quote_blocks,
        "min_chars": min_chars,
    }


def _answer_shape_metrics(answer: str) -> dict[str, int]:
    text = answer.strip()
    # Inline citation markers like [P1], [N3], [12]. These are inline (not
    # block-quote) markers used to ground individual claims in the prose.
    inline_citations = len(re.findall(r"\[[A-Z]?\d+\]", text))
    # Recognize markdown headings (#, ##, ###) AND the bold-as-heading
    # convention Kimi often produces ("**Section Title**\n"). Both are
    # valid section markers in our pipeline; previously the classifier only
    # counted `###` headings and rejected perfectly good 50 k-char drafts
    # because Kimi had used `**Title**` instead.
    md_headings = re.findall(r"^#{1,3}\s+\S", text, flags=re.MULTILINE)
    bold_headings = re.findall(r"^\*\*[^*\n]{2,80}\*\*\s*$", text, flags=re.MULTILINE)
    return {
        "chars": len(text),
        "section_headers": len(md_headings) + len(bold_headings),
        "quote_blocks": len(re.findall(r"^>\s", text, flags=re.MULTILINE)),
        "inline_citations": inline_citations,
    }


# ---------------------------------------------------------------------------
# Progressive render-quality classifier.
#
# Three bands:
#   - "strict":   ≥ min_chars (typically 2,800), ≥ required_sections, and
#                 ≥ 3 inline citations per required section → polish fully.
#   - "llm_short": ≥ 1,800 chars, ≥ max(3, required_sections - 1) sections,
#                 and ≥ 2 inline citations per section → light polish, no
#                 fail. Use Kimi's prose when it is *good but short*.
#   - "inadequate": anything below → fall back to the mechanical renderer.
# ---------------------------------------------------------------------------

# Calibrated for thesis-chapter register. The previous "short" floor of
# 1.8 k chars accepted journal-blog-length answers as "good enough"; doctoral
# work needs at least ~5 k characters of grounded prose with 3-4 citation
# markers per section to be useful.
LLM_SHORT_MIN_CHARS = 5000
LLM_SHORT_MIN_CITATIONS_PER_SECTION = 3
STRICT_MIN_CITATIONS_PER_SECTION = 4


def _classify_render_quality(
    state: RAGState, answer: str
) -> tuple[str, dict[str, int]]:
    """Return ('strict' | 'llm_short' | 'inadequate', metrics).

    Pure function — no side effects. The caller decides what to do per band.
    """
    if not answer or not answer.strip():
        return "inadequate", _answer_shape_metrics("")

    requirements = _render_requirements(state)
    metrics = _answer_shape_metrics(answer)
    chars = metrics["chars"]
    sections = metrics["section_headers"]
    citations = metrics["inline_citations"]
    quote_blocks = metrics["quote_blocks"]
    required_sections = requirements["required_sections"]
    required_quotes = requirements["required_quote_blocks"]
    min_chars = requirements["min_chars"]

    strict_section_target = required_sections or 1
    strict_citations_target = strict_section_target * STRICT_MIN_CITATIONS_PER_SECTION
    strict_ok = (
        chars >= min_chars
        and (not required_sections or sections >= required_sections)
        and (not required_quotes or quote_blocks >= required_quotes)
        and citations >= strict_citations_target
    )
    if strict_ok:
        return "strict", metrics

    # "Massive prose" escape hatch: if the draft is well over 2× the floor
    # with plenty of citations and quote blocks, accept it as ``strict``
    # even when the section header count is short. Previously a 51 k-char
    # draft with 43 inline cites + 20 quote blocks but zero `###` markers
    # (Kimi had used a different heading style) was rejected as
    # "inadequate" and the pipeline fell back to the mechanical renderer.
    massive_ok = (
        chars >= max(min_chars * 2, 12000)
        and citations >= max(strict_citations_target, 12)
        and (not required_quotes or quote_blocks >= max(3, required_quotes - 1))
    )
    if massive_ok:
        return "strict", metrics

    short_section_target = max(3, required_sections - 1) if required_sections else 3
    short_citations_target = short_section_target * LLM_SHORT_MIN_CITATIONS_PER_SECTION
    short_ok = (
        chars >= LLM_SHORT_MIN_CHARS
        and sections >= short_section_target
        and citations >= short_citations_target
    )
    if short_ok:
        return "llm_short", metrics

    # Length-driven fallback: even with few sections, a long draft with
    # decent citation density is better than a 2 k-char mechanical render.
    long_enough_ok = (
        chars >= max(LLM_SHORT_MIN_CHARS, 8000) and citations >= short_citations_target
    )
    if long_enough_ok:
        return "llm_short", metrics

    return "inadequate", metrics


def _answer_is_too_compressed(state: RAGState, answer: str) -> bool:
    """Legacy strict check — kept for callers that need a single boolean.

    The new pipeline should prefer ``_classify_render_quality``.
    """
    band, _metrics = _classify_render_quality(state, answer)
    return band == "inadequate"


def _augment_claim_ledger_from_dossier(
    state: RAGState,
    claims: list[ClaimLedgerItem],
) -> list[ClaimLedgerItem]:
    if not claims:
        return _derive_claim_ledger_fallback(state)

    augmented = _dedupe_claims(list(claims), limit=12)
    fallback_claims = _derive_claim_ledger_fallback(state)
    supported_facets = {
        item.facet_id
        for item in augmented
        if item.facet_id and item.status == ClaimStatus.SUPPORTED and item.evidence_ids
    }
    required_facets = [facet.facet_id for facet in _supported_dossier_facets(state)]
    quote_claims = sum(
        1 for item in augmented if item.quote_original or item.quote_translation
    )
    required_quotes = _render_requirements(state)["required_quote_blocks"]
    target_claim_count = min(10, max(4, len(required_facets) * 2))

    for item in fallback_claims:
        needs_facet = bool(
            item.facet_id
            and item.facet_id in required_facets
            and item.facet_id not in supported_facets
        )
        needs_quote = bool(
            quote_claims < required_quotes
            and (item.quote_original or item.quote_translation)
        )
        needs_density = (
            len(augmented) < target_claim_count and item.support_type == "passage"
        )
        if not (needs_facet or needs_quote or needs_density):
            continue
        augmented.append(item)
        if item.facet_id:
            supported_facets.add(item.facet_id)
        if item.quote_original or item.quote_translation:
            quote_claims += 1
        augmented = _dedupe_claims(augmented, limit=12)
        if (
            len(augmented) >= target_claim_count
            and quote_claims >= required_quotes
            and all(facet_id in supported_facets for facet_id in required_facets)
        ):
            break
    return augmented


def _derive_claim_ledger_fallback(state: RAGState) -> list[ClaimLedgerItem]:
    """Create a conservative ledger when structured drafting fails."""
    dossier = (
        state.scholarly_dossier
        if state.scholarly_dossier.facets
        else _build_scholarly_dossier(state)
    )
    claims: list[ClaimLedgerItem] = []
    ranked_nodes = sorted(
        [item for item in state.all_evidence() if item.type != "passage"],
        key=lambda item: _node_query_score(item, state),
        reverse=True,
    )
    ranked_bundles = sorted(
        state.context_pack.passage_bundles,
        key=lambda bundle: _bundle_score(bundle, state),
        reverse=True,
    )

    if state.query_type == QueryType.SPECIFIC_ENTITY:
        for ev in ranked_nodes[:3]:
            if _node_query_score(ev, state) <= 0:
                continue
            summary = truncate_text(ev.description or _compact_node_line(ev), 220)
            claims.append(
                ClaimLedgerItem(
                    claim=f"{ev.label}: {summary}",
                    evidence_ids=[ev.id],
                    facet_id=(dossier.facets[0].facet_id if dossier.facets else None),
                    evidence_class="metadata",
                    support_type="metadata",
                    confidence=0.6,
                    status=ClaimStatus.SUPPORTED
                    if summary
                    else ClaimStatus.INSUFFICIENT,
                )
            )

    if state.query_type != QueryType.SPECIFIC_ENTITY:
        for ev in ranked_nodes[:4]:
            if _node_query_score(ev, state) <= 0:
                continue
            summary = truncate_text(ev.description or _compact_node_line(ev), 220)
            if not summary:
                continue
            claims.append(
                ClaimLedgerItem(
                    claim=f"{ev.label}: {summary}",
                    evidence_ids=[ev.id],
                    facet_id=(dossier.facets[0].facet_id if dossier.facets else None),
                    evidence_class="metadata",
                    support_type="metadata",
                    confidence=0.7,
                    status=ClaimStatus.SUPPORTED,
                )
            )

    if dossier.facets:
        bundle_lookup = {bundle.bundle_id: bundle for bundle in ranked_bundles}
        node_lookup = {ev.id: ev for ev in ranked_nodes}
        for facet in dossier.facets:
            primary_bundle = next(
                (
                    bundle_lookup[bundle_id]
                    for bundle_id in facet.primary_bundle_ids
                    if bundle_id in bundle_lookup
                ),
                None,
            )
            testimony_bundle = next(
                (
                    bundle_lookup[bundle_id]
                    for bundle_id in facet.testimony_bundle_ids
                    if bundle_id in bundle_lookup
                ),
                None,
            )
            counter_bundle = next(
                (
                    bundle_lookup[bundle_id]
                    for bundle_id in facet.counter_bundle_ids
                    if bundle_id in bundle_lookup
                ),
                None,
            )
            metadata_node = next(
                (
                    node_lookup[node_id]
                    for node_id in facet.metadata_ids
                    if node_id in node_lookup
                ),
                None,
            )
            lead_bundle = primary_bundle or testimony_bundle or counter_bundle
            evidence_ids = list(
                dict.fromkeys(
                    [
                        *(
                            facet.primary_bundle_ids[:2]
                            if facet.primary_bundle_ids
                            else []
                        ),
                        *(
                            facet.testimony_bundle_ids[:2]
                            if facet.testimony_bundle_ids
                            else []
                        ),
                        *(
                            facet.counter_bundle_ids[:1]
                            if facet.counter_bundle_ids
                            else []
                        ),
                        *(facet.metadata_ids[:1] if facet.metadata_ids else []),
                    ]
                )
            )
            if not evidence_ids and not metadata_node:
                continue
            if primary_bundle is not None:
                direct_labels = [
                    _bundle_label(bundle_lookup[bundle_id])
                    for bundle_id in facet.primary_bundle_ids[:2]
                    if bundle_id in bundle_lookup
                ]
                claim_text = f"{facet.title}: direct textual evidence centers on {', '.join(direct_labels)}."
                if testimony_bundle is not None:
                    claim_text = (
                        claim_text[:-1]
                        + f"; ancillary ancient testimony is preserved by {_bundle_label(testimony_bundle)}."
                    )
            elif testimony_bundle is not None:
                claim_text = (
                    f"{facet.title}: the surviving evidence is chiefly indirect, especially in "
                    f"{_bundle_label(testimony_bundle)}."
                )
            elif metadata_node is not None:
                summary = truncate_text(
                    metadata_node.description or _compact_node_line(metadata_node), 220
                )
                claim_text = f"{facet.title}: {metadata_node.label} frames the issue as {summary}."
            else:
                continue
            claims.append(
                ClaimLedgerItem(
                    claim=claim_text,
                    evidence_ids=evidence_ids,
                    facet_id=facet.facet_id,
                    evidence_class=(
                        _bundle_academic_features(lead_bundle, state)["evidence_class"]
                        if lead_bundle is not None
                        else "metadata"
                    ),
                    quote_original=truncate_text(lead_bundle.original_text, 240)
                    if lead_bundle is not None
                    else None,
                    quote_translation=truncate_text(lead_bundle.translation_text, 240)
                    if lead_bundle is not None and lead_bundle.translation_text
                    else None,
                    support_type="passage" if lead_bundle is not None else "metadata",
                    confidence=0.7,
                    status=ClaimStatus.SUPPORTED,
                )
            )
            if lead_bundle is not None:
                quote_original = _bundle_quote_excerpt(lead_bundle, limit=260)
                quote_translation = _bundle_quote_excerpt(
                    lead_bundle,
                    prefer_translation=True,
                    limit=260,
                )
                if quote_original or quote_translation:
                    claims.append(
                        ClaimLedgerItem(
                            claim=(
                                f"{facet.title}: {_bundle_label(lead_bundle)} provides a textual anchor for this issue."
                            ),
                            evidence_ids=[lead_bundle.bundle_id],
                            facet_id=facet.facet_id,
                            evidence_class=_bundle_academic_features(
                                lead_bundle, state
                            )["evidence_class"],
                            quote_original=quote_original,
                            quote_translation=quote_translation,
                            support_type="passage",
                            confidence=0.68,
                            status=ClaimStatus.SUPPORTED,
                        )
                    )
            if counter_bundle is not None:
                claims.append(
                    ClaimLedgerItem(
                        claim=(
                            f"{facet.title}: an important complication appears in {_bundle_label(counter_bundle)}."
                        ),
                        evidence_ids=[counter_bundle.bundle_id],
                        facet_id=facet.facet_id,
                        evidence_class="counter_evidence",
                        quote_original=_bundle_quote_excerpt(counter_bundle, limit=220),
                        quote_translation=_bundle_quote_excerpt(
                            counter_bundle,
                            prefer_translation=True,
                            limit=220,
                        ),
                        support_type="passage",
                        confidence=0.62,
                        status=ClaimStatus.SUPPORTED,
                    )
                )
    else:
        for bundle in ranked_bundles[: min(8, len(ranked_bundles))]:
            claim = f"{bundle.author or 'The text'} addresses the question in {bundle.work_title}"
            if bundle.canonical_ref:
                claim += f" at {bundle.canonical_ref}"
            claims.append(
                ClaimLedgerItem(
                    claim=claim,
                    evidence_ids=[bundle.bundle_id],
                    evidence_class=_bundle_academic_features(bundle, state)[
                        "evidence_class"
                    ],
                    quote_original=truncate_text(bundle.original_text, 240),
                    quote_translation=truncate_text(bundle.translation_text, 240)
                    if bundle.translation_text
                    else None,
                    support_type="passage",
                    confidence=0.65,
                    status=ClaimStatus.SUPPORTED,
                )
            )

    if not claims:
        for ev in ranked_nodes[:3]:
            summary = truncate_text(ev.description or _compact_node_line(ev), 180)
            claims.append(
                ClaimLedgerItem(
                    claim=f"{ev.label}: {summary}",
                    evidence_ids=[ev.id],
                    facet_id=(dossier.facets[0].facet_id if dossier.facets else None),
                    evidence_class="metadata",
                    support_type="metadata",
                    confidence=0.45,
                    status=ClaimStatus.INSUFFICIENT
                    if state.insufficient_evidence
                    else ClaimStatus.SUPPORTED,
                )
            )
    return _dedupe_claims(claims, limit=12)


def _normalize_quote_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip('"“”')).lower()


def _extract_line_refs(line: str) -> list[str]:
    refs: list[str] = []
    for block in REF_RE.findall(line):
        for token in re.findall(r"P?\d+", block):
            if (token.startswith("P") and token[1:].isdigit()) or token.isdigit():
                refs.append(token)
    return refs


def _normalize_reference_markers(line: str, refs: list[str]) -> str:
    if not refs:
        return line

    allowed = list(dict.fromkeys(refs))
    allowed_set = set(allowed)

    def _replace_block(match: re.Match[str]) -> str:
        block_refs: list[str] = []
        for token in re.findall(r"P?\d+", match.group(1)):
            canonical = token if token.startswith("P") else token
            if canonical in allowed_set and canonical not in block_refs:
                block_refs.append(canonical)
        if not block_refs:
            return ""
        return "[" + ", ".join(block_refs) + "]"

    normalized = REF_RE.sub(_replace_block, line)
    while "[[" in normalized or "]]" in normalized:
        normalized = normalized.replace("[[", "[").replace("]]", "]")
    normalized = re.sub(r"\]\[", "] [", normalized)
    normalized = re.sub(r"\[\s*\]", "", normalized)

    present = set(_extract_line_refs(normalized))
    missing = [ref for ref in allowed if ref not in present]
    if missing:
        suffix = " ".join(f"[{ref}]" for ref in missing)
        normalized = f"{normalized.rstrip()} {suffix}".strip()

    normalized = re.sub(r"\s{2,}", " ", normalized)
    return normalized.strip()


# ``_fold_ancient_text`` / ``_contains_word_bounded`` are imported from
# ``ancient_text_matching`` (shared with the post-synthesis text verifier).


def _collect_ref_source_texts(
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
) -> list[str]:
    source_texts: list[str] = []
    for ref in refs:
        if ref in bundles_by_ref:
            bundle = bundles_by_ref[ref]
            source_texts.extend(
                text for text in (bundle.original_text, bundle.translation_text) if text
            )
        elif ref in nodes_by_ref:
            evidence = nodes_by_ref[ref]
            source_texts.extend(
                text for text in (evidence.description, evidence.text_content) if text
            )
    return source_texts


def _split_elided_segments(text: str) -> list[str]:
    """Split an elided quotation on ellipsis tokens into checkable segments."""
    return [segment for segment in ELLIPSIS_RE.split(text) if segment.strip()]


def _segments_in_order(text: str, segments: list[str]) -> bool:
    """True when every segment matches word-bounded, in order, in ``text``.

    Each segment must start at a strictly later offset than the end of the
    previous match (an ellipsis elides material *between* segments, so a
    later segment can never precede or overlap an earlier one). Greedy
    earliest matching is optimal here: taking the first possible match for
    each segment leaves maximal room for the remaining ones.
    """
    position = 0
    for segment in segments:
        index = _word_bounded_index(text, segment, position)
        if index < 0:
            return False
        position = index + len(segment)
    return True


def _segments_supported_by_text(segments: list[str], text: str) -> bool:
    """Every elided segment must exist verbatim — and in order — in this text.

    The segments of one elided quotation must appear at increasing offsets
    within a single representation of the source (normalized, else folded):
    real fragments quoted out of their source order are a stitched
    fabrication, not an elision.
    """
    if _segments_in_order(
        _normalize_quote_text(text),
        [_normalize_quote_text(segment) for segment in segments],
    ):
        return True
    return _segments_in_order(
        _fold_ancient_text(text),
        [_fold_ancient_text(segment) for segment in segments],
    )


def _quote_supported_by_refs(
    quote: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
) -> bool:
    normalized_quote = _normalize_quote_text(quote)
    # Ancient-language spans are never waved through: any quote containing
    # Greek must be checked from 2 word-chars up; plain Latin-script quotes
    # keep the looser 6-char floor for incidental short phrases.
    min_word_chars = 2 if GREEK_CHAR_RE.search(quote) else 6
    if len(re.sub(r"\W+", "", normalized_quote)) < min_word_chars:
        return True
    source_texts = _collect_ref_source_texts(refs, bundles_by_ref, nodes_by_ref)
    segments = _split_elided_segments(quote)
    return any(_segments_supported_by_text(segments, text) for text in source_texts)


def _combined_greek_misses(line: str, folded_sources: list[str]) -> list[str]:
    """Validate a quotation line's Greek as ordered whole-line segments.

    A blockquote stitched together from isolated real fragments — single
    words or genuine multi-word spans split into separate runs by em-dashes
    or other separators the run regex does not cross — must not pass by
    validating each fragment independently. Between ellipsis tokens, the
    line's Greek must be one contiguous span of a single cited source, and
    successive segments must occur in source order at increasing offsets —
    real segments quoted in reverse order are a stitched fabrication.
    Returns the original runs when unsupported, ``[]`` when the combined
    check passes.
    """
    segments: list[str] = []
    for piece in ELLIPSIS_RE.split(line):
        joined = _fold_ancient_text(
            " ".join(run for run, _pos in extract_greek_runs(piece))
        )
        if len(re.sub(r"\W+", "", joined)) >= 2:
            segments.append(joined)
    if not segments:
        return []
    if any(_segments_in_order(source, segments) for source in folded_sources):
        return []
    return [run for run, _pos in extract_greek_runs(line)]


def _unsupported_greek_runs(
    line: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
    min_words: int = 1,
    combine_short_runs: bool = False,
) -> list[str]:
    """Greek runs in a quoted line that are absent from the cited evidence.

    ``min_words`` lets prose lines tolerate short inline technical terms
    while still rejecting sentence-length unverified Greek.
    ``combine_short_runs`` (quotation-formatted lines) re-combines multiple
    runs into ordered whole-line segments: real fragments assembled into a
    fake quotation — single words or genuine multi-word spans stitched with
    em-dashes — must be checked as one contiguous sequence, not one by one.
    """
    runs = extract_greek_runs(line)
    if not runs:
        return []
    folded_sources = [
        _fold_ancient_text(text)
        for text in _collect_ref_source_texts(refs, bundles_by_ref, nodes_by_ref)
    ]
    if combine_short_runs and len(runs) >= 2:
        return _combined_greek_misses(line, folded_sources)
    unsupported: list[str] = []
    for run, _pos in runs:
        # An ASCII "..." glues two elided segments into one run; each
        # segment must exist verbatim — in source order — in a single
        # cited source.
        segments = [
            folded
            for folded in (
                _fold_ancient_text(part) for part in _split_elided_segments(run)
            )
            if len(re.sub(r"\W+", "", folded)) >= 2
        ]
        if not segments:
            continue
        if sum(len(segment.split()) for segment in segments) < min_words:
            continue
        if not any(_segments_in_order(source, segments) for source in folded_sources):
            unsupported.append(run)
    return unsupported


def _unsupported_latin_quotation(
    line: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
) -> str | None:
    """Unquoted Latin-script text in a quotation-formatted line that looks
    ancient (no modern function words) and is absent from the cited evidence.
    """
    text = QUOTE_RE.sub(" ", line)
    text = REF_RE.sub(" ", text)
    text = text.lstrip("> ").strip()
    if not text or GREEK_CHAR_RE.search(text):
        return None
    folded_sources: list[str] | None = None
    for chunk in LATIN_CHUNK_SPLIT_RE.split(text):
        segments = [
            folded
            for folded in (
                _fold_ancient_text(part) for part in _split_elided_segments(chunk)
            )
            if folded
        ]
        words = [word for segment in segments for word in segment.split()]
        # Short chunks (attributions, page refs) and anything carrying a
        # modern function word are prose, not candidate ancient Latin.
        if len(words) < 5 or any(word in MODERN_STOPWORDS for word in words):
            continue
        if folded_sources is None:
            folded_sources = [
                _fold_ancient_text(source)
                for source in _collect_ref_source_texts(
                    refs, bundles_by_ref, nodes_by_ref
                )
            ]
        if not any(
            all(_contains_word_bounded(source, segment) for segment in segments)
            for source in folded_sources
        ):
            return chunk.strip()
    return None


def _sanitize_line_quotes(
    line: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
    unsupported_quotes: list[str] | None = None,
) -> str | None:
    matches = list(QUOTE_RE.finditer(line))
    if not matches:
        return line

    for match in matches:
        quote = next(group for group in match.groups() if group is not None)
        if _quote_supported_by_refs(quote, refs, bundles_by_ref, nodes_by_ref):
            continue
        # Drop the whole line: stripping the quote marks while keeping the
        # text would launder an unverifiable quotation into plain prose.
        if unsupported_quotes is not None:
            unsupported_quotes.append(quote)
        return None
    return line


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    return len(stripped) <= 80 and stripped.endswith(":") and stripped.count(" ") <= 8


def _verify_answer_programmatically(
    state: RAGState, _depth: int = 0
) -> tuple[str, list[Citation]]:
    """Keep only grounded lines and emit citations for the surviving refs."""
    bundles_by_ref, nodes_by_ref = _reverse_ref_maps(state)
    valid_refs = set(bundles_by_ref) | set(nodes_by_ref)
    kept_lines: list[str] = []
    unsupported_quotes: list[str] = []
    seen_refs: set[str] = set()
    pending_headers: list[str] = []
    pending_blank = False

    def _flush_pending_structure() -> None:
        nonlocal pending_blank, pending_headers
        if pending_headers:
            if kept_lines and kept_lines[-1] != "":
                kept_lines.append("")
            kept_lines.extend(pending_headers)
            pending_headers = []
        elif pending_blank and kept_lines and kept_lines[-1] != "":
            kept_lines.append("")
        pending_blank = False

    raw_lines = state.raw_answer.splitlines()
    index = 0
    while index < len(raw_lines):
        raw_line = raw_lines[index]
        line = raw_line.strip()
        index += 1
        if not line:
            pending_blank = bool(kept_lines or pending_headers)
            continue
        if _is_section_header(line):
            if pending_blank and kept_lines and kept_lines[-1] != "":
                kept_lines.append("")
            pending_headers.append(line)
            pending_blank = False
            continue
        if line.startswith(">"):
            block_lines = [line]
            while index < len(raw_lines):
                next_line = raw_lines[index].strip()
                if not next_line.startswith(">"):
                    break
                block_lines.append(next_line)
                index += 1

            block_refs = list(
                dict.fromkeys(
                    ref
                    for block_line in block_lines
                    for ref in _extract_line_refs(block_line)
                    if ref in valid_refs
                )
            )
            if not block_refs:
                continue

            _flush_pending_structure()
            for block_line in block_lines:
                if block_line == ">":
                    if kept_lines and kept_lines[-1] != ">":
                        kept_lines.append(">")
                    continue
                refs = [
                    ref for ref in _extract_line_refs(block_line) if ref in valid_refs
                ] or block_refs
                sanitized = _sanitize_line_quotes(
                    block_line, refs, bundles_by_ref, nodes_by_ref, unsupported_quotes
                )
                if not sanitized:
                    continue
                # Blockquotes are quotations by format: every Greek run must
                # exist verbatim (modulo accents/final sigma/punctuation) in
                # the cited evidence, quoted or not — and lines assembled
                # from isolated single words are checked as one sequence.
                greek_misses = _unsupported_greek_runs(
                    sanitized,
                    refs,
                    bundles_by_ref,
                    nodes_by_ref,
                    combine_short_runs=True,
                )
                if greek_misses:
                    unsupported_quotes.extend(greek_misses)
                    continue
                # Same rule for unquoted ancient Latin in quotation format.
                latin_miss = _unsupported_latin_quotation(
                    sanitized, refs, bundles_by_ref, nodes_by_ref
                )
                if latin_miss:
                    unsupported_quotes.append(latin_miss)
                    continue
                kept_lines.append(_normalize_reference_markers(sanitized, refs))
            seen_refs.update(block_refs)
            continue
        refs = _extract_line_refs(line)
        valid_line_refs = [ref for ref in refs if ref in valid_refs]
        if not valid_line_refs:
            continue
        line = _sanitize_line_quotes(
            line, valid_line_refs, bundles_by_ref, nodes_by_ref, unsupported_quotes
        )
        if not line:
            continue
        # Prose lines tolerate short inline Greek terms, but sentence-length
        # unverified Greek (4+ words) is fabrication regardless of format.
        greek_misses = _unsupported_greek_runs(
            line, valid_line_refs, bundles_by_ref, nodes_by_ref, min_words=4
        )
        if greek_misses:
            unsupported_quotes.extend(greek_misses)
            continue
        line = _normalize_reference_markers(line, valid_line_refs)
        _flush_pending_structure()
        kept_lines.append(line)
        seen_refs.update(valid_line_refs)

    if unsupported_quotes:
        recorded = state.metadata.setdefault("unsupported_quotes", [])
        recorded.extend(quote for quote in unsupported_quotes if quote not in recorded)

    if not kept_lines:
        fallback = _render_answer_fallback(state)
        state.raw_answer = fallback
        if _depth > 0 or not _extract_line_refs(fallback):
            return fallback, []
        return _verify_answer_programmatically(state, _depth=_depth + 1)

    citations: list[Citation] = []
    for ref in sorted(
        seen_refs,
        key=lambda value: (
            not value.startswith("P"),
            int(value[1:] if value.startswith("P") else value),
        ),
    ):
        if ref in bundles_by_ref:
            bundle = bundles_by_ref[ref]
            citations.append(
                Citation(
                    ref=ref,
                    type="passage",
                    id=bundle.original_passage_id,
                    label=_bundle_label(bundle),
                    layer=EvidenceLayer.PRIMARY,
                    verified=True,
                    verification_note=(
                        "Reference resolved to evidence bundle; quoted ancient "
                        "text checked for containment"
                    ),
                )
            )
        elif ref in nodes_by_ref:
            ev = nodes_by_ref[ref]
            citations.append(
                Citation(
                    ref=ref,
                    type="node",
                    id=ev.id,
                    label=ev.label,
                    layer=ev.layer,
                    confidence=ev.confidence,
                    verified=True,
                    verification_note=(
                        "Reference resolved to packed metadata; quoted text "
                        "checked for containment"
                    ),
                )
            )

    return "\n".join(kept_lines), citations


def _dialectical_citations(state: RAGState) -> list[Citation]:
    """Build the structured citation list for the dialectical (Scholar-RAG)
    answer from its prose-derived provenance ledger.

    The dialectical prose cites inline via ``[P_*]``/``[passage_*]``/``[edge:*]``
    markers; :func:`build_provenance_ledger` already resolved those against the
    ControversyMap into ``state.claim_ledger``. We surface:

    - each SUPPORTED PASSAGE item as a PRIMARY ``Citation`` (ancient source), and
    - each SUPPORTED POSITION item as a SECONDARY ``Citation`` — a FIRST-CLASS
      modern-scholarship reference (scholar, work, page), so the frontend
      ``CitationGenerator`` can export it alongside the primary sources (a real
      scholar's answer enters dialogue with named scholars, and those scholar
      citations must be citable — not only ancient passages).

    Edge items are structural links, not citations. Deterministic, no LLM call.

    Resolution discipline (GOAL-8, B1-B3): a citation ``label`` must NEVER be a
    raw node id. We resolve each ``evidence_id`` against — in order — the
    ALREADY-RESOLVED in-memory ControversyMap (``PassageRef`` /
    ``GroundedPosition``, which carry author/work/holder/publication resolved at
    map build), then the evidence bundles, then the in-memory KG node lookup. The
    raw id is kept ONLY as ``Citation.id`` (clickability), never as the label.
    """
    # B1 — resolution maps from the ALREADY-RESOLVED in-memory ControversyMap
    # (mirror build_provenance_ledger: positions keyed by position_id, passages
    # by passage_id over contested_passages + exegesis_units + provenance).
    pos_by_id: dict[str, GroundedPosition] = {}
    passage_by_id: dict[str, PassageRef] = {}
    cmap = state.controversy_map
    if cmap is not None:
        for frame in cmap.frames:
            for pos in frame.positions:
                pos_by_id[pos.position_id] = pos
                if pos.holder_node_id:
                    pos_by_id[pos.holder_node_id] = pos
            for pr in frame.contested_passages:
                passage_by_id[pr.passage_id] = pr
        for pr in cmap.exegesis_units:
            passage_by_id[pr.passage_id] = pr
        for pid, pr in cmap.provenance.items():
            passage_by_id[pid] = pr
    # node_lookup: in-memory KG node dicts/Evidence by id (no DB call).
    node_lookup: dict[str, Evidence] = {ev.id: ev for ev in state.all_evidence()}

    citations: list[Citation] = []
    seen: set[str] = set()
    for item in state.claim_ledger:
        if item.status != ClaimStatus.SUPPORTED:
            continue
        if item.support_type == "passage":
            for ev_id in item.evidence_ids:
                if ev_id in seen:
                    continue
                seen.add(ev_id)
                # B2 — passage label resolver: (a) PassageRef from the map,
                # (b) evidence bundle, (c) node_lookup label, (d) raw id.
                label = ev_id
                cts_urn: str | None = None
                pr = passage_by_id.get(ev_id)
                if pr is not None:
                    label = " ".join(
                        part
                        for part in (
                            f"{pr.author}, {pr.work}".strip(", ").strip(),
                            pr.canonical_ref.strip(),
                        )
                        if part
                    ).strip()
                    cts_urn = pr.cts_urn or None
                if not label or label == ev_id:
                    bundle_label = _bundle_label_from_id(state, ev_id)
                    if bundle_label and bundle_label != ev_id:
                        label = bundle_label
                if (not label or label == ev_id) and ev_id in node_lookup:
                    node_label = (node_lookup[ev_id].label or "").strip()
                    if node_label:
                        label = node_label
                        cts_urn = cts_urn or node_lookup[ev_id].cts_urn
                citations.append(
                    Citation(
                        ref=ev_id,
                        type="passage",
                        id=ev_id,  # KEEP id for clickability
                        label=label or ev_id,
                        layer=EvidenceLayer.PRIMARY,
                        confidence=item.confidence,
                        verified=True,
                        cts_urn=cts_urn,
                        verification_note=(
                            "Dialectical synthesis: inline marker resolved to a "
                            "ControversyMap passage (cite-as-you-write provenance)"
                        ),
                    )
                )
        elif item.support_type == "position":
            # A named modern scholar's position → a citable SECONDARY reference.
            # evidence_ids[0] is the holder/position node id.
            ev_id = item.evidence_ids[0] if item.evidence_ids else ""
            if not ev_id or ev_id in seen:
                continue
            seen.add(ev_id)
            # B3 — position label resolver: (a) GroundedPosition from the map →
            # format_scholar_reference; (b) publication metadata via node_lookup;
            # (c) quote_translation (ledger-carried reference); (d) node label.
            # NEVER let the label equal the raw id; NEVER invent a year/page.
            label = ""
            doi: str | None = None
            pos = pos_by_id.get(ev_id)
            if pos is not None:
                if pos.holder:
                    label = format_scholar_reference(pos)
                if not label and pos.publication_node_id:
                    label, doi = _resolve_publication(
                        pos.publication_node_id, node_lookup
                    )
                if not label and pos.publication:
                    label = pos.publication.strip()
            if not label:
                pub_label, pub_doi = _resolve_publication(ev_id, node_lookup)
                label = pub_label
                doi = doi or pub_doi
            if not label and item.quote_translation:
                qt = item.quote_translation.strip()
                if qt and qt != ev_id:
                    label = qt
            if not label and ev_id in node_lookup:
                node_label = (node_lookup[ev_id].label or "").strip()
                if node_label and node_label != ev_id:
                    label = node_label
            # Degrade gracefully: if nothing resolved, OMIT rather than leak the id.
            if not label or label == ev_id:
                continue
            citations.append(
                Citation(
                    ref=ev_id,
                    type="node",
                    id=ev_id,  # KEEP id for clickability
                    label=label,
                    layer=EvidenceLayer.SECONDARY,
                    confidence=item.confidence,
                    verified=True,
                    doi=doi or None,
                    verification_note=(
                        "Dialectical synthesis: inline [P_*] marker resolved to a "
                        "ControversyMap modern-scholar position (scholar + "
                        "publication + page; cite-as-you-write provenance)"
                    ),
                )
            )
    return citations


def _resolve_publication(
    node_id: str, node_lookup: dict[str, Evidence]
) -> tuple[str, str | None]:
    """Resolve a publication/scholar node id to a human reference + DOI.

    Builds "Surname, Initials (year). Title. Place: Publisher." from whatever
    KG metadata is present — NEVER inventing a missing year, page, or publisher
    (degrade to "Author, Title" or just the node label). Returns ("", None) when
    the id is absent or carries nothing human-readable, so the caller can OMIT
    rather than leak a raw id. Treats an empty-string DOI as absent.
    """
    ev = node_lookup.get(node_id)
    if ev is None:
        return "", None
    meta = ev.metadata or {}

    def _g(*keys: str) -> str:
        for k in keys:
            v = meta.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""

    author = _g("author", "scholar", "surname")
    year = _g("year", "publication_year", "date")
    title = _g("title", "work", "label") or (ev.label or "").strip()
    publisher = _g("publisher")
    place = _g("place", "city")
    journal = _g("journal")
    doi_raw = _g("doi")
    doi = doi_raw or None

    parts: list[str] = []
    head = author
    if year:
        head = f"{head} ({year})" if head else f"({year})"
    if head:
        parts.append(head)
    if title and title != author:
        parts.append(title)
    if journal:
        parts.append(journal)
    elif publisher:
        parts.append(f"{place}: {publisher}" if place else publisher)
    label = ". ".join(p for p in parts if p).strip()
    if label and not label.endswith("."):
        label += "."
    if not label:
        return "", doi
    return label, doi


def _grounding_score(requested_refs: set[str], citations: list[Citation]) -> int:
    """Ref-resolution coverage: how much of the draft's claimed grounding
    survived programmatic verification.

    Ratio of refs in the raw (pre-verification) answer that resolved to a
    verified citation, on a 0-100 scale. This is NOT a semantic claim-support
    check — an unquoted fabricated claim citing a resolvable ref still scores
    100 here; only the v2 adversarial verifier audits claim support. The
    metric's basis is recorded in ``metadata['grounding']['method']``
    ('ref_resolution'), and the v2 verifier later overwrites both score and
    method (with its audited-sample coverage) when it runs. When the raw
    answer carried no refs at all, a deterministic fallback that emitted
    citations is fully grounded by construction (100); no refs and no
    citations is 0.
    """
    resolved_refs = {citation.ref for citation in citations}
    if requested_refs:
        return int(
            round(100 * len(resolved_refs & requested_refs) / len(requested_refs))
        )
    return 100 if resolved_refs else 0


def _quality_badge_from_state(state: RAGState) -> str:
    if state.metadata.get("pipeline_degraded"):
        return "Low"
    score = max(int(state.sufficiency_score * 100), 0)
    if score >= 80 and state.citations:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _make_answer(state: RAGState) -> ScholarlyAnswer:
    return ScholarlyAnswer(
        answer=state.raw_answer,
        question=state.question,
        complexity=state.complexity,
        query_type=state.query_type,
        citations=state.citations,
        seed_nodes=state.seed_node_ids,
        context_nodes=state.context_node_ids,
        passages_used=state.passages_used,
        iterations=max(1, state.iteration + 1),
        sub_queries=state.sub_queries,
        quality_badge=state.quality_badge,
        self_rag_evaluation=state.self_rag_evaluation,
        crag_validation=state.crag_validation,
        insufficient_evidence=state.insufficient_evidence,
        grounding_policy=state.grounding_policy,
        claim_ledger=state.claim_ledger,
        metadata=state.metadata,
    )


def _select_passage_anchors(
    valid_anchors: list[str],
    strategy_anchors: list[str],
    node_lookup: dict[str, Any],
) -> list[str]:
    """Merge KG anchors with database passage UUIDs from the strategy.

    SQLStrategy returns raw ``passages.passage_id`` UUIDs that are not KG
    node ids; they must survive into bundle building rather than being
    discarded by the node_lookup membership filter.
    """
    combined = list(valid_anchors)
    for anchor in strategy_anchors:
        anchor_id = str(anchor)
        if anchor_id in combined:
            continue
        if anchor_id in node_lookup or _PASSAGE_UUID_RE.match(anchor_id):
            combined.append(anchor_id)
    return combined[:12]


def _ensure_notebook(state: RAGState) -> ResearchNotebook:
    if not state.research_notebook:
        state.research_notebook = ResearchNotebook()
    return state.research_notebook


@dataclass
class ClassifyQueryType(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Classify query type and initialize pipeline config and budgets."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandQuery:
        # ``ExpandQuery`` lives in ``legacy_fsm_nodes`` (FSM-only). Import
        # lazily to keep the dependency one-directional; the FSM graph in
        # ``scholarly_agent`` resolves the return annotation through its own
        # namespace, and the react path ignores the returned node entirely.
        from eleutheria_graphrag.agents.legacy_fsm_nodes import ExpandQuery

        state = ctx.state
        model_api_id = _resolve_model_api_id(state)
        heuristic_query_type = _default_query_type(state.question)
        if heuristic_query_type == QueryType.SPECIFIC_ENTITY:
            query_type = heuristic_query_type
            confidence = 0.75
            reason = "deterministic heuristic"
            _append_reasoning_step(
                state,
                "ClassifyQueryType",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="deterministic heuristic (SPECIFIC_ENTITY)",
            )
        else:
            _classify_prompt = CLASSIFY_QUERY_TYPE_PROMPT.format(
                question=state.question
            )
            try:
                _t0 = _time.time()
                raw = await ctx.deps.llm.generate(
                    _classify_prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.0,
                    max_tokens=256,
                    cache_key="query-classifier",
                    cache_prefix="query_classifier_v1",
                    model_override=model_api_id,
                    tier="utility",
                )
                _dur = int((_time.time() - _t0) * 1000)
                parsed = ClassificationResult.model_validate(_parse_json(raw))
                query_type = parsed.query_type
                confidence = parsed.confidence
                reason = parsed.reason
                _append_reasoning_step(
                    state,
                    "ClassifyQueryType",
                    ctx.deps.llm.last_model_used or state.selected_model,
                    _classify_prompt[:200],
                    len(_classify_prompt) // 4,
                    raw,
                    duration_ms=_dur,
                    parsed_result={
                        "query_type": query_type.value,
                        "confidence": confidence,
                        "reason": reason,
                    },
                )
            except Exception:
                query_type = heuristic_query_type
                confidence = 0.45
                reason = "heuristic fallback"
                _append_reasoning_step(
                    state,
                    "ClassifyQueryType",
                    None,
                    _classify_prompt[:200],
                    len(_classify_prompt) // 4,
                    "",
                    skipped=True,
                    skip_reason="LLM call failed, heuristic fallback",
                )

        state.query_type = query_type
        state.pipeline_config = get_pipeline_config(query_type)
        state.complexity = query_type_to_complexity(query_type)
        state.metadata["query_type"] = query_type.value
        state.metadata["classification_confidence"] = confidence
        state.metadata["classification_reason"] = reason
        _trace_stage(
            state,
            "classify_query",
            {
                "mode": "heuristic" if "heuristic" in reason.lower() else "llm",
                "query_type": query_type.value,
                "confidence": round(float(confidence), 4),
                "reason": reason,
                "complexity": state.complexity.value,
            },
        )
        return ExpandQuery()


async def assess_evidence_sufficiency(
    state: RAGState,
    deps: Deps,
) -> tuple[float, bool, str, str | None]:
    """Core sufficiency check shared by the FSM node and the react pipeline.

    Computes the heuristic coverage score, optionally asks the LLM for a
    judgement, and records the outcome on ``state`` (sufficiency_score,
    insufficient_evidence, crag_validation, reasoning trace). Returns
    ``(score, sufficient, reason, refinement)`` so callers can decide
    whether to grant a bounded continuation round.
    """
    notebook = _ensure_notebook(state)
    bundle_count = len(state.context_pack.passage_bundles)
    work_count = len({bundle.work_id for bundle in state.context_pack.passage_bundles})
    counter_count = len(notebook.counter_evidence)
    dossier = (
        state.scholarly_dossier
        if state.scholarly_dossier.facets
        else _build_scholarly_dossier(state)
    )
    covered_facets = sum(
        1
        for facet in dossier.facets
        if facet.primary_bundle_ids or facet.testimony_bundle_ids or facet.metadata_ids
    )
    heuristic_score = min(
        1.0,
        0.12 * bundle_count
        + 0.08 * work_count
        + 0.1 * counter_count
        + 0.08 * covered_facets,
    )
    model_api_id = _resolve_model_api_id(state)
    if _should_minimize_llm_calls(state):
        score = heuristic_score
        sufficient = score >= 0.45
        reason = "heuristic sufficiency (minimal llm mode)"
        refinement = None
        _append_reasoning_step(
            state,
            "EvidenceSufficiency",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="minimal-llm mode, heuristic only",
            parsed_result={
                "score": round(heuristic_score, 4),
                "sufficient": sufficient,
            },
        )
    else:
        _suff_prompt = SUFFICIENCY_PROMPT.format(
            question=state.question,
            bundle_count=bundle_count,
            work_count=work_count,
            counter_count=counter_count,
            open_questions=", ".join(notebook.open_questions[:5]) or "(none)",
        )
        try:
            _t0 = _time.time()
            raw = await deps.llm.generate(
                _suff_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=256,
                cache_key="evidence-sufficiency",
                cache_prefix="evidence_sufficiency_v1",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            assessment = SufficiencyAssessment.model_validate(_parse_json(raw))
            score = max(heuristic_score, assessment.score)
            sufficient = assessment.sufficient
            reason = assessment.reason
            refinement = assessment.refinement
            _append_reasoning_step(
                state,
                "EvidenceSufficiency",
                deps.llm.last_model_used or state.selected_model,
                _suff_prompt[:200],
                len(_suff_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={
                    "score": round(score, 4),
                    "sufficient": sufficient,
                    "reason": reason,
                },
            )
        except Exception:
            score = heuristic_score
            sufficient = score >= 0.45
            reason = "heuristic sufficiency"
            refinement = None
            _append_reasoning_step(
                state,
                "EvidenceSufficiency",
                None,
                _suff_prompt[:200],
                len(_suff_prompt) // 4,
                "",
                skipped=True,
                skip_reason="LLM call failed, heuristic fallback",
            )

    state.sufficiency_score = score
    state.insufficient_evidence = not sufficient
    state.crag_validation = CRAGValidation(
        relevance=int(min(100, score * 100)),
        completeness=int(min(100, (0.5 * bundle_count + 5 * work_count))),
        confidence=int(min(100, score * 100)),
        missing=notebook.open_questions[:3] if not sufficient else [],
        suggestions=[refinement] if refinement else [],
    )
    _trace_stage(
        state,
        "evidence_sufficiency",
        {
            "bundle_count": bundle_count,
            "work_count": work_count,
            "counter_count": counter_count,
            "covered_facets": covered_facets,
            "score": round(score, 4),
            "sufficient": sufficient,
            "reason": reason,
            "refinement": refinement,
        },
    )
    return score, sufficient, reason, refinement


@dataclass
class DraftClaimLedger(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Draft a structured claim ledger before prose generation."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> RenderGroundedAnswer:
        state = ctx.state
        model_api_id = _resolve_model_api_id(state)
        notebook = _ensure_notebook(state)
        if not state.context_pack.prompt_context:
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context
        dossier = _build_scholarly_dossier(state)
        default_facet_id = next(
            (
                facet.facet_id
                for facet in dossier.facets
                if "textual" in facet.title.lower()
                or "definition" in facet.title.lower()
            ),
            dossier.facets[0].facet_id if dossier.facets else None,
        )

        direct_quote_bundle = _select_direct_quote_bundle(state)
        if direct_quote_bundle is not None:
            state.claim_ledger = [
                ClaimLedgerItem(
                    claim=f"{direct_quote_bundle.author or 'Unknown author'}, {direct_quote_bundle.work_title} {direct_quote_bundle.canonical_ref or ''}".strip(),
                    evidence_ids=[direct_quote_bundle.bundle_id],
                    facet_id=default_facet_id,
                    evidence_class=_bundle_academic_features(
                        direct_quote_bundle, state
                    )["evidence_class"],
                    quote_original=truncate_text(
                        direct_quote_bundle.original_text, 1400
                    ),
                    quote_translation=truncate_text(
                        direct_quote_bundle.translation_text, 1400
                    )
                    if direct_quote_bundle.translation_text
                    else None,
                    support_type="passage",
                    confidence=1.0,
                    status=ClaimStatus.SUPPORTED,
                )
            ]
            _attach_proof_chains(state, ctx.deps, state.claim_ledger)
            notebook.claim_ledger = state.claim_ledger
            state.metadata["claim_ledger_mode"] = "deterministic_quote"
            _append_reasoning_step(
                state,
                "DraftClaimLedger",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="deterministic quote bundle",
                parsed_result={
                    "mode": "deterministic_quote",
                    "bundle_id": direct_quote_bundle.bundle_id,
                },
            )
            _trace_stage(
                state,
                "draft_claim_ledger",
                {
                    "mode": "deterministic_quote",
                    "bundle_id": direct_quote_bundle.bundle_id,
                    "canonical_ref": direct_quote_bundle.canonical_ref,
                },
            )
            _update_insufficiency_flags_from_claims(state)
            return RenderGroundedAnswer()

        raw = ""
        try:
            evidence_catalog = _claim_ledger_catalog(state)
            _ledger_prompt = CLAIM_LEDGER_PROMPT.format(
                question=state.question,
                grounding_policy=state.grounding_policy.value,
                notebook_json=truncate_json(notebook.model_dump(), 12000),
                dossier_json=truncate_json(_scholarly_dossier_payload(state), 16000),
                evidence_catalog_json=truncate_json(evidence_catalog, 12000),
                context=truncate_text(state.context_pack.prompt_context, 30000),
            )
            _t0 = _time.time()
            raw = await ctx.deps.llm.generate(
                _ledger_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=3800,
                response_mime_type="application/json",
                response_json_schema=CLAIM_LEDGER_RESPONSE_SCHEMA,
                cache_key="claim-ledger",
                cache_prefix="claim_ledger_v2",
                model_override=model_api_id,
                tier="utility",
            )
            _dur = int((_time.time() - _t0) * 1000)
            parsed = _coerce_claim_ledger_payload(_parse_json(raw))
            valid_ids = set(state.context_pack.bundle_refs) | set(
                state.context_pack.node_refs
            )
            claims = [
                ClaimLedgerItem(
                    claim=item.claim,
                    evidence_ids=_resolve_claim_evidence_ids(
                        [str(eid) for eid in item.evidence_ids],
                        item.support_type,
                        state,
                    ),
                    facet_id=item.facet_id or default_facet_id,
                    evidence_class=item.evidence_class
                    or (
                        "metadata" if item.support_type == "metadata" else "direct_text"
                    ),
                    quote_original=item.quote_original,
                    quote_translation=item.quote_translation,
                    support_type=_normalize_claim_support_type(item.support_type),
                    confidence=item.confidence,
                    status=item.status,
                )
                for item in parsed.claims
                if item.claim
            ]
            claims = [
                item
                for item in claims
                if any(eid in valid_ids for eid in item.evidence_ids)
            ]
            claims = _augment_claim_ledger_from_dossier(state, claims)
            _append_reasoning_step(
                state,
                "DraftClaimLedger",
                ctx.deps.llm.last_model_used or state.selected_model,
                _ledger_prompt[:200],
                len(_ledger_prompt) // 4,
                raw,
                duration_ms=_dur,
                parsed_result={"claim_count": len(claims)},
            )
            _trace_stage(
                state,
                "draft_claim_ledger",
                {
                    "mode": "llm",
                    "claim_count": len(claims),
                    "raw_excerpt": truncate_text(raw, 2000),
                },
            )
        except Exception as exc:
            _append_reasoning_step(
                state,
                "DraftClaimLedger",
                None,
                _ledger_prompt[:200],
                len(_ledger_prompt) // 4,
                raw or "",
                skipped=True,
                skip_reason=f"LLM call failed: {type(exc).__name__}",
            )
            claims = []
            salvaged = _salvage_claim_ledger(raw) if raw else None
            if salvaged is not None:
                valid_ids = set(state.context_pack.bundle_refs) | set(
                    state.context_pack.node_refs
                )
                claims = [
                    ClaimLedgerItem(
                        claim=item.claim,
                        evidence_ids=_resolve_claim_evidence_ids(
                            [str(eid) for eid in item.evidence_ids],
                            item.support_type,
                            state,
                        ),
                        facet_id=item.facet_id or default_facet_id,
                        evidence_class=item.evidence_class
                        or (
                            "metadata"
                            if item.support_type == "metadata"
                            else "direct_text"
                        ),
                        quote_original=item.quote_original,
                        quote_translation=item.quote_translation,
                        support_type=_normalize_claim_support_type(item.support_type),
                        confidence=item.confidence,
                        status=item.status,
                    )
                    for item in salvaged.claims
                    if item.claim
                ]
                claims = [
                    item
                    for item in claims
                    if any(eid in valid_ids for eid in item.evidence_ids)
                ]
                if claims:
                    claims = _augment_claim_ledger_from_dossier(state, claims)
                    _trace_stage(
                        state,
                        "draft_claim_ledger",
                        {
                            "mode": "llm_salvaged",
                            "error": f"{type(exc).__name__}: {exc}",
                            "claim_count": len(claims),
                            "raw_excerpt": truncate_text(raw, 2000),
                        },
                    )
                    state.metadata["claim_ledger_mode"] = "llm_salvaged"
                    _attach_proof_chains(state, ctx.deps, claims)
                    state.claim_ledger = claims
                    notebook.claim_ledger = claims
                    _update_insufficiency_flags_from_claims(state)
                    return RenderGroundedAnswer()
            _trace_stage(
                state,
                "draft_claim_ledger",
                {
                    "mode": "fallback",
                    "error": f"{type(exc).__name__}: {exc}",
                    "raw_excerpt": truncate_text(raw, 2000) if raw else "",
                },
            )

        if not claims:
            claims = _derive_claim_ledger_fallback(state)
            if _heuristic_claim_ledger_acceptable(state, claims):
                state.metadata["claim_ledger_mode"] = "heuristic"
            else:
                state.metadata["claim_ledger_mode"] = "fallback"
                state.metadata["pipeline_degraded"] = True
        else:
            state.metadata["claim_ledger_mode"] = "llm"

        claims = _augment_claim_ledger_from_dossier(state, claims)
        _attach_proof_chains(state, ctx.deps, claims)
        state.claim_ledger = claims
        notebook.claim_ledger = claims
        _update_insufficiency_flags_from_claims(state)
        return RenderGroundedAnswer()


def build_render_prompt(state: RAGState) -> dict[str, Any]:
    """Build the grounded-answer render prompt and its supporting payloads.

    Shared by the blocking :class:`RenderGroundedAnswer` graph node and the
    streaming render path in ``ScholarlyAgent.query_stream`` so both produce
    byte-identical prompts. Returns a dict whose ``mode`` is either
    ``"deterministic_quote"`` (``answer`` is final — no LLM call needed) or
    ``"llm"`` (``prompt`` / ``requirements`` drive generation; the dossier,
    evidence packet and reference map are returned too for the node's
    expand-retry and polish passes).
    """
    model_api_id = _resolve_model_api_id(state)
    if not state.claim_ledger:
        state.claim_ledger = _derive_claim_ledger_fallback(state)
    dossier_payload = _scholarly_dossier_payload(state)

    if state.metadata.get("claim_ledger_mode") == "deterministic_quote":
        quote_item = state.claim_ledger[0]
        ref = next(
            (
                state.context_pack.bundle_refs[eid]
                for eid in quote_item.evidence_ids
                if eid in state.context_pack.bundle_refs
            ),
            None,
        )
        lines = [quote_item.claim]
        if quote_item.quote_original and ref:
            lines.append(f'Greek original: "{quote_item.quote_original}" [{ref}]')
        if quote_item.quote_translation and ref:
            lines.append(
                f'English translation: "{quote_item.quote_translation}" [{ref}]'
            )
        return {
            "mode": "deterministic_quote",
            "model_api_id": model_api_id,
            "answer": "\n".join(lines).strip(),
        }

    reference_map = {
        item.claim: _claim_reference_markers(state, item) for item in state.claim_ledger
    }
    evidence_packet = _render_evidence_packet(state)
    requirements = _render_requirements(state)

    render_prompt = RENDER_ANSWER_PROMPT.format(
        question=state.question,
        ledger_json=truncate_json(
            [item.model_dump() for item in state.claim_ledger],
            12000,
        ),
        dossier_json=truncate_json(dossier_payload, 16000),
        reference_json=truncate_json(reference_map, 6000),
        evidence_packet_json=truncate_json(evidence_packet, 14000),
        required_sections=requirements["required_sections"],
        required_quote_blocks=requirements["required_quote_blocks"],
    )
    return {
        "mode": "llm",
        "model_api_id": model_api_id,
        "prompt": render_prompt,
        "requirements": requirements,
        "dossier_payload": dossier_payload,
        "evidence_packet": evidence_packet,
        "reference_map": reference_map,
    }


@dataclass
class RenderGroundedAnswer(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Render prose from the claim ledger using stable prompt caching."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ProgrammaticVerify:
        state = ctx.state
        _payload = build_render_prompt(state)
        model_api_id = _payload["model_api_id"]

        if _payload["mode"] == "deterministic_quote":
            state.raw_answer = _payload["answer"]
            state.metadata["render_answer_mode"] = "deterministic_quote"
            _append_reasoning_step(
                state,
                "RenderGroundedAnswer",
                None,
                "",
                0,
                "",
                skipped=True,
                skip_reason="deterministic quote rendering",
            )
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": "deterministic_quote",
                    "raw_excerpt": truncate_text(state.raw_answer, 2000),
                },
            )
            return ProgrammaticVerify()

        dossier_payload = _payload["dossier_payload"]
        evidence_packet = _payload["evidence_packet"]
        reference_map = _payload["reference_map"]
        requirements = _payload["requirements"]
        _render_prompt = _payload["prompt"]
        raw_answer = ""
        try:
            _t0 = _time.time()
            raw_answer = await ctx.deps.llm.generate(
                _render_prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                # Doctoral-length renders need headroom — chapter sections
                # at 1500-2500 words apiece quickly cross 6 k completion
                # tokens. 16 k leaves room for 8-10 sections.
                max_tokens=16000,
                cache_key="render-grounded-answer",
                cache_prefix="render_grounded_answer_v3",
                model_override=model_api_id,
            )
            _render_dur = int((_time.time() - _t0) * 1000)
            rendered_answer = raw_answer.strip()

            # ----- Progressive render-quality classification -----------------
            band, _shape = _classify_render_quality(state, rendered_answer)
            expand_retry_count = 0
            minimize_calls = _should_minimize_llm_calls(state)

            # One-shot expand retry when the first draft lands in the
            # llm_short band (or below): ask the model to deepen the existing
            # exegesis without adding new claims. Skip if we're in a
            # minimal-call regime (cheap eval runs).
            if (
                band in ("llm_short", "inadequate")
                and rendered_answer
                and not minimize_calls
            ):
                try:
                    expand_prompt = EXPAND_RETRY_PROMPT.format(
                        question=state.question,
                        current_chars=_shape["chars"],
                        current_sections=_shape["section_headers"],
                        # Aim for the doctoral floor (10 k chars) at minimum
                        # on retry, going higher if the dossier supports it.
                        target_chars=max(requirements["min_chars"], 10000),
                        dossier_json=truncate_json(dossier_payload, 14000),
                        evidence_packet_json=truncate_json(evidence_packet, 12000),
                        reference_json=truncate_json(reference_map, 6000),
                        draft_answer=truncate_text(rendered_answer, 24000),
                    )
                    expanded_answer = await ctx.deps.llm.generate(
                        expand_prompt,
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.15,
                        max_tokens=16000,
                        cache_key="render-expand-retry",
                        cache_prefix="render_expand_retry_v2",
                        model_override=model_api_id,
                    )
                    expanded_answer = expanded_answer.strip()
                    expand_retry_count = 1
                    if expanded_answer:
                        new_band, _new_shape = _classify_render_quality(
                            state, expanded_answer
                        )
                        # Accept the expansion if it strictly improved the
                        # band or stayed in the same usable band but got
                        # longer. Reject if it regressed.
                        band_rank = {"strict": 2, "llm_short": 1, "inadequate": 0}
                        if band_rank[new_band] > band_rank[band] or (
                            band_rank[new_band] == band_rank[band]
                            and _new_shape["chars"] > _shape["chars"]
                        ):
                            rendered_answer = expanded_answer
                            band = new_band
                            _shape = _new_shape
                    _trace_stage(
                        state,
                        "render_expand_retry",
                        {
                            "attempted": True,
                            "from_band": band,
                            "shape_metrics": _shape,
                        },
                    )
                except Exception as exc:
                    _trace_stage(
                        state,
                        "render_expand_retry",
                        {
                            "attempted": True,
                            "error": f"{type(exc).__name__}: {exc}",
                        },
                    )

            state.metadata["expand_retry_count"] = expand_retry_count

            # ----- Polishing pass --------------------------------------------
            # Polish prose-quality drafts (strict + llm_short). Skip for
            # inadequate drafts (no point polishing a fallback) and for
            # minimal-call regimes.
            #
            _polish_mode = "skipped"
            _enable_polish = (
                os.getenv(
                    "ELEUTHERIA_RENDER_POLISH",
                    "auto",
                )
                .strip()
                .lower()
            )
            _polish_allowed = _enable_polish in {"1", "true", "yes", "on", "auto"}
            if (
                band in ("strict", "llm_short")
                and not minimize_calls
                and _polish_allowed
            ):
                polish_max_tokens = 4800 if band == "strict" else 3200
                try:
                    polished_answer = await ctx.deps.llm.generate(
                        SCHOLARLY_POLISH_PROMPT.format(
                            question=state.question,
                            dossier_json=truncate_json(dossier_payload, 14000),
                            draft_answer=truncate_text(rendered_answer, 18000),
                        ),
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.1,
                        max_tokens=polish_max_tokens,
                        cache_key=f"scholarly-polish-{band}",
                        cache_prefix="scholarly_polish_v2",
                        model_override=model_api_id,
                    )
                    polished_answer = polished_answer.strip()
                    if polished_answer:
                        rendered_answer = polished_answer
                        polish_label = "llm" if band == "strict" else "llm_short"
                        state.metadata["scholarly_polish_mode"] = polish_label
                        _polish_mode = polish_label
                        _trace_stage(
                            state,
                            "scholarly_polish",
                            {
                                "mode": polish_label,
                                "raw_excerpt": truncate_text(polished_answer, 2000),
                            },
                        )
                except Exception as exc:
                    state.metadata["scholarly_polish_mode"] = "fallback"
                    _polish_mode = "fallback"
                    _trace_stage(
                        state,
                        "scholarly_polish",
                        {
                            "mode": "fallback",
                            "error": f"{type(exc).__name__}: {exc}",
                        },
                    )
            compression_repair_mode = "skipped"
            # Compression repair disabled — programmatic passage injection
            # in scholarly_agent._inject_passage_quotations handles this instead
            if False:
                try:
                    repaired_answer = await ctx.deps.llm.generate(
                        COMPRESSION_REPAIR_PROMPT.format(
                            question=state.question,
                            required_sections=requirements["required_sections"],
                            required_quote_blocks=requirements["required_quote_blocks"],
                            facet_titles="\n".join(
                                f"- {facet.title}"
                                for facet in _supported_dossier_facets(state)
                            )
                            or "- General answer",
                            dossier_json=truncate_json(dossier_payload, 16000),
                            ledger_json=truncate_json(
                                [item.model_dump() for item in state.claim_ledger],
                                12000,
                            ),
                            draft_answer=truncate_text(rendered_answer, 18000),
                        ),
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.1,
                        max_tokens=3600,
                        cache_key="compression-repair",
                        cache_prefix="compression_repair_v1",
                        model_override=model_api_id,
                    )
                    repaired_answer = repaired_answer.strip()
                    if repaired_answer:
                        rendered_answer = repaired_answer
                        compression_repair_mode = "llm"
                except Exception:
                    compression_repair_mode = "fallback"
                    logger.warning("Compression repair failed", exc_info=True)
            state.metadata["compression_repair_mode"] = compression_repair_mode
            _total_dur = int((_time.time() - _t0) * 1000)
            _append_reasoning_step(
                state,
                "RenderGroundedAnswer",
                ctx.deps.llm.last_model_used or state.selected_model,
                _render_prompt[:200],
                len(_render_prompt) // 4,
                raw_answer,
                duration_ms=_total_dur,
                parsed_result={
                    "synthesis_ms": _render_dur,
                    "polish_mode": _polish_mode,
                    "compression_mode": compression_repair_mode,
                },
            )

            # Re-classify after polish: polish can shrink or expand prose,
            # so the final band may differ from the post-expand band.
            final_band, _final_shape = _classify_render_quality(state, rendered_answer)
            fallback_answer = _render_answer_fallback(state)
            if not rendered_answer or final_band == "inadequate":
                rendered_answer = fallback_answer
                final_band = "inadequate"
            state.raw_answer = rendered_answer
            fallback_used = state.raw_answer == fallback_answer
            if fallback_used:
                state.metadata["render_answer_mode"] = "fallback"
                state.metadata["pipeline_degraded"] = True
            elif final_band == "strict":
                state.metadata["render_answer_mode"] = "llm"
            else:
                # llm_short: prose-quality answer below strict threshold but
                # above llm_short floor — NOT a fallback.
                state.metadata["render_answer_mode"] = "llm_short"
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": state.metadata["render_answer_mode"],
                    "raw_excerpt": truncate_text(state.raw_answer, 2000),
                    "polish_mode": state.metadata.get(
                        "scholarly_polish_mode", "skipped"
                    ),
                    "compression_repair_mode": compression_repair_mode,
                    "render_requirements": requirements,
                    "shape_metrics": _answer_shape_metrics(state.raw_answer),
                    "expand_retry_count": expand_retry_count,
                    "render_band": final_band,
                },
            )
        except Exception as exc:
            _append_reasoning_step(
                state,
                "RenderGroundedAnswer",
                None,
                _render_prompt[:200],
                len(_render_prompt) // 4,
                raw_answer or "",
                skipped=True,
                skip_reason=f"LLM call failed: {type(exc).__name__}",
            )
            state.raw_answer = _render_answer_fallback(state)
            state.metadata["render_answer_mode"] = "fallback"
            state.metadata["pipeline_degraded"] = True
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": "fallback",
                    "error": f"{type(exc).__name__}: {exc}",
                    "raw_excerpt": truncate_text(raw_answer, 2000)
                    if raw_answer
                    else "",
                },
            )

        return ProgrammaticVerify()


@dataclass
class ProgrammaticVerify(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Programmatic answer verification and citation emission."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> End[ScholarlyAnswer]:
        state = ctx.state
        _t0 = _time.time()
        # Scholar-RAG M4: the dialectical answer carries its OWN inline marker
        # scheme ([P_*]/[passage_*]/[edge:*]) and is NOT a [B1]/[N3] line-ref
        # render. The legacy line-pruner (_verify_answer_programmatically) would
        # drop every prose line (no numeric refs resolve) and replace the answer
        # with the facet fallback — defeating the cutover. On this path we PRESERVE
        # the prose verbatim and derive citations from the prose-built provenance
        # ledger; the adversarial verifier-v2 + scholar verification do the real
        # claim audit. Legacy path is byte-for-byte unchanged.
        if state.metadata.get("render_answer_mode") == "dialectical":
            requested_refs = set(_extract_line_refs(state.raw_answer))
            answer = state.raw_answer
            citations = _dialectical_citations(state)
        else:
            requested_refs = set(_extract_line_refs(state.raw_answer))
            answer, citations = _verify_answer_programmatically(state)
        _dur = int((_time.time() - _t0) * 1000)
        state.raw_answer = answer
        state.citations = citations
        _append_reasoning_step(
            state,
            "ProgrammaticVerify",
            None,
            "",
            0,
            "",
            skipped=True,
            skip_reason="no LLM call (programmatic verification)",
            duration_ms=_dur,
            parsed_result={"citation_count": len(citations)},
        )
        _trace_stage(
            state,
            "programmatic_verify",
            {
                "citation_count": len(citations),
                "answer_excerpt": truncate_text(answer, 1200),
            },
        )
        state.quality_badge = _quality_badge_from_state(state)
        score = int(max(0, min(100, state.sufficiency_score * 100)))
        grounding = _grounding_score(requested_refs, citations)
        state.metadata["grounding"] = {
            "score": grounding,
            "method": "ref_resolution",
            "requested_refs": len(requested_refs),
            "resolved_refs": len({c.ref for c in citations} & requested_refs),
        }
        state.self_rag_evaluation = SelfRAGEvaluation(
            relevance=score,
            grounding=grounding,
            completeness=score,
            confidence=score,
            caveats=state.research_notebook.uncertainties[:3],
            improvements=[],
        )
        state.metadata["research_graph"] = _build_research_graph_payload(state)
        return End(_make_answer(state))
