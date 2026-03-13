"""
pydantic-graph FSM nodes for the long-context scholarly GraphRAG pipeline.

The active pipeline is:

    ClassifyQueryType
      -> ExpandQuery
      -> DiscoverCorpus
      -> BuildResearchNotebook
      -> TreeNavigateWorks
      -> ExpandEvidenceBundles
      -> SeekCounterEvidence
      -> EvidenceSufficiency
      -> DraftClaimLedger
      -> RenderGroundedAnswer
      -> ProgrammaticVerify
      -> End

Legacy node names are kept as thin wrappers where that improves compatibility,
but the shared helpers implement a single structured-agent flow.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import deque
from dataclasses import dataclass
from typing import Any

from pydantic_graph import BaseNode, End, GraphRunContext

from eleutheria_graphrag.agents.dependencies import Deps
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
    QueryComplexity,
    RAGState,
    ReadingNote,
    ReadingDecision,
    ResearchFacet,
    ResearchNotebook,
    ResearchToolCall,
    RetrievalBudget,
    ScholarlyAnswer,
    ScholarlyDossier,
)
from eleutheria_graphrag.agents.structured_models import (
    ClaimLedgerDraft,
    ClaimLedgerDraftItem,
    ClassificationResult,
    CounterEvidenceResult,
    CRAGValidation,
    ExpansionTerms,
    ResearchFrame,
    ReadingPlanResult,
    SelfRAGEvaluation,
    SufficiencyAssessment,
    TreeNavigationResult,
)
from eleutheria_graphrag.agents.text_utils import truncate_json, truncate_text

logger = logging.getLogger(__name__)

DB_SCHEMA = os.getenv("ELEUTHERIA_DB_SCHEMA", "free_will")
LINE_SPLIT_RE = re.compile(r"\n+")
REF_RE = re.compile(r"\[(.*?)\]")
REF_NUMBER_RE = re.compile(r"\b\d+\b")
QUOTE_RE = re.compile(r"[\"“](.+?)[\"”]")
TERM_RE = re.compile(r"[A-Za-zÀ-ÿἀ-῾']+")
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
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
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
You are a research assistant for ancient philosophy.

Rules:
- Work like a careful scholar: frame the question, inspect structure, gather
  evidence, seek counter-evidence, then answer.
- Never invent Greek or Latin. Quote original text exactly if it exists in the
  provided evidence bundles.
- Treat doctrinal claims as passage-first. Knowledge-graph facts may support
  authorship, chronology, school affiliation, and translation linkage.
- If the evidence is partial, say so explicitly instead of smoothing over gaps.
- Every substantive line in the final answer must carry one or more citations.
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
- Return 6-10 claims when evidence permits, and never more than 12.
- Keep each claim to 1 sentence.
- Keep quote_original and quote_translation short (<= 180 characters each) and omit them when not needed.
- Keep the ledger concise, high-signal, and organized around facets rather than retrieval order.

Return only JSON:
{{"claims": [{{"claim": "...", "evidence_ids": ["..."], "facet_id": "...", "evidence_class": "direct_text|ancient_testimony|metadata|counter_evidence", "quote_original": "...", "quote_translation": "...", "support_type": "passage|metadata", "confidence": 0.0-1.0, "status": "supported|insufficient"}}]}}
"""

RENDER_ANSWER_PROMPT = """\
Render a polished, grounded scholarly answer from this claim ledger, dossier, and evidence packet.

Question: {question}
Claim ledger:
{ledger_json}

Dossier:
{dossier_json}

Reference map:
{reference_json}

Evidence packet:
{evidence_packet_json}

Requirements:
- Use only the provided references and evidence packet.
- Every substantial paragraph or quotation block must end with at least one reference marker.
- Write like a first-rate historian of ancient philosophy, not like a retrieval log.
- Begin with a short thesis paragraph, then use 2-5 markdown section headers drawn from the dossier facets.
- Cover at least {required_sections} dossier-driven sections if the dossier contains that many supported facets.
- Include at least {required_quote_blocks} quotation blocks when the dossier/ledger already contains quoted evidence.
- Separate major sections with blank lines.
- Prefer coherent prose with short section headers over bullet lists unless bullets genuinely improve readability.
- Structure the answer around the dossier facets rather than around retrieval order.
- Distinguish clearly between:
  - direct textual evidence from ancient sources
  - ancient testimony or doxography
  - modern scholarly framing or metadata
  - your own synthesis
- For the strongest facets, include short quotation blocks with the original Greek/Latin and the paired translation immediately after it when available.
- If the best evidence is only indirect, say so plainly rather than presenting it as a direct Stoic text.
- Never invent Greek, Latin, or translations.
- If the ledger contains insufficient items, state that cautiously and explain the limit of the evidence.
- Keep the answer elegant and continuous; do not sound like notes pasted from a notebook.
- Do not collapse the whole answer into a single paragraph.
- Do not introduce any uncited sentence.
"""

SCHOLARLY_POLISH_PROMPT = """\
You are performing a final scholarly prose pass on an already grounded answer.

Question: {question}
Dossier:
{dossier_json}

Draft answer:
{draft_answer}

Rules:
- Preserve every existing citation marker exactly.
- Do not introduce any new fact not already present in the draft answer or dossier.
- Improve prose, transitions, and section structure so the answer reads like a finished scholarly response.
- Preserve the distinction between direct textual evidence, ancient testimony, and synthesis.
- Keep Greek/Latin quotes verbatim if they already appear.
- Ensure the answer retains a thesis paragraph, meaningful section headers, and at least one quotation block when the draft already contains quoted evidence.
- Keep blank-line paragraph breaks between major sections.
- If the draft is note-like, convert it into polished prose without dropping citations.
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
    """Extract JSON from LLM output, stripping markdown code fences."""
    def _repair_json(candidate: str) -> str:
        candidate = (
            candidate.replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
        )
        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        candidate = re.sub(r":\s*NaN\b", ": null", candidate)
        candidate = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
        return candidate

    text = text.strip()
    if text.lower().startswith("json"):
        text = text[4:].lstrip(": \n\t")
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    elif text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, count=1).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _repair_json(text)
        if repaired != text:
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        candidates: list[str] = []
        start_obj = text.find("{")
        start_arr = text.find("[")
        if start_obj != -1:
            end_obj = text.rfind("}")
            if end_obj != -1 and end_obj > start_obj:
                candidates.append(text[start_obj : end_obj + 1])
        if start_arr != -1:
            end_arr = text.rfind("]")
            if end_arr != -1 and end_arr > start_arr:
                candidates.append(text[start_arr : end_arr + 1])
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                repaired = _repair_json(candidate)
                if repaired != candidate:
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass
        raise


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
        part for part in (state.question, state.expanded_query or "", *state.sub_queries) if part
    ).lower()
    return any(token in haystack for token in ("quote", "quotation", "cite", "citation", "citer"))


def _question_reference_numbers(state: RAGState) -> tuple[str, ...]:
    haystack = " ".join(
        part for part in (state.question, state.expanded_query or "", *state.sub_queries) if part
    )
    return tuple(dict.fromkeys(REF_NUMBER_RE.findall(haystack)))


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "facet"


def _question_school_hints(state: RAGState) -> set[str]:
    hints: set[str] = set()
    haystack = " ".join(
        part for part in (state.question, state.expanded_query or "", *state.sub_queries) if part
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
                    keywords=["difference", "divergence", "contrast", *sorted(terms)[:4]],
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
                        keywords=["text", "passage", "testimony", "evidence", *sorted(terms)[:5]],
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
                title="Causal Mechanism" if not doctrinal_query else "Causal Structure of Fate",
                question=f"What causal mechanism or explanatory structure do the sources give for {question}?",
                keywords=["cause", "causal", "determinism", "fate", "necessity"],
                priority=2,
            )
        )
    if terms & {"responsibility", "assent", "freedom", "choice", "prohairesis", "moral"}:
        facets.append(
            _make_research_facet(
                title="Agency and Responsibility",
                question=f"How do the sources connect {question} to agency, assent, responsibility, or freedom?",
                keywords=["agency", "assent", "responsibility", "freedom", "choice", "prohairesis"],
                priority=3,
            )
        )
    if doctrinal_query:
        facets.append(
            _make_research_facet(
                title="Ancient Testimony and Preservation",
                question=f"Through which ancient witnesses, reports, or preserved fragments do we know the evidence for {question}?",
                keywords=["testimony", "preservation", "report", "fragment", *sorted(school_hints)],
                priority=4,
            )
        )
    if school_hints or state.query_type in {QueryType.GLOBAL_ABSTRACT, QueryType.MULTI_HOP, QueryType.COMPARATIVE}:
        facets.append(
            _make_research_facet(
                title="Counterpoint and Nuance" if not doctrinal_query else "Counterpoints and Limits",
                question=f"What counter-evidence, disagreement, or textual nuance complicates {question}?",
                keywords=["counterpoint", "nuance", "disagreement", "objection", *sorted(school_hints)],
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


def _normalize_notebook_facets(state: RAGState, facets: list[ResearchFacet]) -> list[ResearchFacet]:
    if not facets:
        return _default_research_facets(state)

    normalized: list[ResearchFacet] = []
    seen: set[str] = set()
    for index, facet in enumerate(facets, start=1):
        facet_id = facet.facet_id or _slugify(facet.title or facet.question or f"facet-{index}")
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


def _bundle_academic_features(bundle: EvidenceBundle, state: RAGState) -> dict[str, Any]:
    profile = _author_profile_for_name(state, bundle.author)
    author_hints = _question_author_hints(state)
    school_hints = _question_school_hints(state)
    label_haystack = " ".join(part for part in (bundle.author, bundle.work_title, bundle.section_path) if part).lower()
    author_match = any(hint in label_haystack for hint in author_hints)
    school_value = str(profile.get("school") or bundle.metadata.get("author_school") or "").lower()
    school_match = bool(school_hints and school_value and any(hint in school_value for hint in school_hints))
    work_priority_rank = next(
        (
            index
            for index, title in enumerate(state.research_notebook.work_priorities[:20], start=1)
            if title.lower() == bundle.work_title.lower()
        ),
        None,
    )
    evidence_class = "direct_text"
    if bundle.evidence_role == "counter_evidence":
        evidence_class = "counter_evidence"
    elif school_hints and not school_match and not author_match:
        evidence_class = "ancient_testimony"

    period = str(profile.get("period") or bundle.metadata.get("author_period") or "").lower()
    late_penalty = 0
    if evidence_class == "ancient_testimony" and any(
        hint in period for hint in ("late", "imperial", "medieval", "byzantine", "christian")
    ):
        late_penalty = 8

    facet_overlap = 0
    for facet in state.research_notebook.facets:
        facet_terms = _tokenize_terms(" ".join([facet.title, facet.question, *facet.keywords]))
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
        facet_overlap = max(facet_overlap, sum(1 for term in facet_terms if term in haystack))

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


def _facet_bundle_score(bundle: EvidenceBundle, facet: ResearchFacet, state: RAGState) -> int:
    facet_terms = _tokenize_terms(" ".join([facet.title, facet.question, *facet.keywords]))
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
            truncate_text(bundle.translation_text, 1600) if bundle.translation_text else "",
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
    if facet.title.lower().startswith("counterpoint") or "nuance" in facet.title.lower():
        evidence_bonus = 16 if features["evidence_class"] == "counter_evidence" else evidence_bonus
    return overlap * 18 + evidence_bonus + _bundle_query_score(bundle, state)


def _facet_node_score(ev: Evidence, facet: ResearchFacet, state: RAGState) -> int:
    facet_terms = _tokenize_terms(" ".join([facet.title, facet.question, *facet.keywords]))
    if not facet_terms:
        return _node_query_score(ev, state)
    haystack = " ".join(
        part for part in (ev.label, ev.type, ev.description, ev.period, ev.school, ev.role) if part
    ).lower()
    return sum(1 for term in facet_terms if term in haystack) * 14 + _node_query_score(ev, state)


def _bundle_label_from_id(state: RAGState, bundle_id: str) -> str:
    for bundle in state.evidence_bundles:
        if bundle.bundle_id == bundle_id:
            return _bundle_label(bundle)
    return bundle_id


def _bundle_quote_excerpt(bundle: EvidenceBundle, *, prefer_translation: bool = False, limit: int = 220) -> str | None:
    text = (
        bundle.translation_text
        if prefer_translation and bundle.translation_text
        else bundle.original_text or bundle.translation_text
    )
    if not text:
        return None
    return truncate_text(text, limit)


def _diversify_bundles(bundles: list[EvidenceBundle], *, max_per_work: int) -> list[EvidenceBundle]:
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
            ev.id
            for ev in ranked_nodes[:3]
            if _facet_node_score(ev, facet, state) > 0
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
            summary = f"Direct textual evidence centers on {', '.join(primary_labels[:2])}."
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
                    & set(primary_ids_for_facet + testimony_ids_for_facet + counter_ids_for_facet)
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
    dossier = state.scholarly_dossier if state.scholarly_dossier.facets else _build_scholarly_dossier(state)
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
            "evidence_class": _bundle_academic_features(bundle, state)["evidence_class"],
            "quote_original_excerpt": _bundle_quote_excerpt(bundle),
            "quote_translation_excerpt": _bundle_quote_excerpt(bundle, prefer_translation=True),
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


def _stage_summary(stage_id: str, payload: dict[str, Any] | None, state: RAGState) -> str:
    if stage_id == "classify_query":
        query_type = state.metadata.get("query_type") or getattr(state.query_type, "value", state.query_type)
        confidence = state.metadata.get("classification_confidence")
        mode = payload.get("mode") if payload else None
        conf_text = (
            f"{round(float(confidence) * 100)}% confidence"
            if isinstance(confidence, float | int)
            else "heuristic confidence"
        )
        if query_type:
            return f"{query_type} selected with {conf_text}" + (f" via {mode}" if mode else "")
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


def _stage_metrics(stage_id: str, payload: dict[str, Any] | None, state: RAGState) -> list[dict[str, Any]]:
    if stage_id == "classify_query":
        metrics = [
            {"label": "Type", "value": state.metadata.get("query_type") or getattr(state.query_type, "value", state.query_type)},
            {"label": "Complexity", "value": state.complexity.value},
        ]
        confidence = state.metadata.get("classification_confidence")
        if isinstance(confidence, float | int):
            metrics.append({"label": "Confidence", "value": f"{round(float(confidence) * 100)}%"})
        if payload and payload.get("mode"):
            metrics.append({"label": "Mode", "value": payload["mode"]})
        return metrics

    if stage_id == "expand_query":
        terms = state.expansion_terms
        return [
            {"label": "Philosophers", "value": len(getattr(terms, "philosophers", []) or [])},
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
            ("Translations", sum(1 for item in payload.get("bundle_sample", []) if item.get("translation_source"))),
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
            ("Score", f"{round(float(score) * 100)}%" if isinstance(score, float | int) else score),
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

    tool_count = sum(1 for item in state.research_notebook.tool_calls if item.stage_id == stage_id)
    decision_count = sum(1 for item in state.research_notebook.reading_decisions if item.stage_id == stage_id)
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
    dossier = state.scholarly_dossier if state.scholarly_dossier.facets else _build_scholarly_dossier(state)
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
                "primary_count": len(dossier_facet.primary_bundle_ids) if dossier_facet else 0,
                "testimony_count": len(dossier_facet.testimony_bundle_ids) if dossier_facet else 0,
                "counter_count": len(dossier_facet.counter_bundle_ids) if dossier_facet else 0,
                "metadata_count": len(dossier_facet.metadata_ids) if dossier_facet else 0,
                "note_count": len(dossier_facet.note_ids) if dossier_facet else 0,
                "uncertainty_count": len(dossier_facet.uncertainties) if dossier_facet else 0,
            }
        )

    work_map: dict[str, dict[str, Any]] = {}
    for section in state.metadata.get("selected_sections", []):
        work_id = str(section.get("work_id") or "unknown")
        work = work_map.setdefault(
            work_id,
            {
                "work_id": work_id,
                "title": section.get("work_title") or section.get("title") or "Unknown work",
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
            bundle_refs[eid]
            if eid in bundle_refs
            else node_refs[eid]
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
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "evidence_ids": item.evidence_ids,
                "refs": refs,
                "quote_original": truncate_text(item.quote_original, 240) if item.quote_original else None,
                "quote_translation": truncate_text(item.quote_translation, 240) if item.quote_translation else None,
            }
        )

    return {
        "overview": {
            "query_type": state.metadata.get("query_type") or getattr(state.query_type, "value", state.query_type),
            "complexity": state.complexity.value,
            "grounding_policy": state.grounding_policy.value,
            "quality_badge": state.quality_badge,
            "pipeline_degraded": bool(state.metadata.get("pipeline_degraded")),
            "claim_ledger_mode": state.metadata.get("claim_ledger_mode", "unknown"),
            "render_answer_mode": state.metadata.get("render_answer_mode", "unknown"),
            "scholarly_polish_mode": state.metadata.get("scholarly_polish_mode", "skipped"),
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
            truncate_text(bundle.translation_text, 1200) if bundle.translation_text else "",
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
        if bundle.canonical_ref and re.search(rf"\b{re.escape(ref_number)}\b", bundle.canonical_ref):
            ref_bonus += 50 if _question_requests_quote(state) else 25
        elif bundle.section_path and re.search(rf"\b{re.escape(ref_number)}\b", bundle.section_path):
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
    scored_bundles: list[tuple[tuple[int, int, int], EvidenceBundle]],
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


def _merge_expansion_terms(primary: ExpansionTerms, fallback: ExpansionTerms) -> ExpansionTerms:
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
                    key = tuple(str(item.get(part, "")).strip().lower() for part in keys)
                else:
                    key = tuple(str(getattr(item, part, "")).strip().lower() for part in keys)
                if not any(key):
                    continue
                if key in seen:
                    continue
                seen.add(key)
                merged.append(item)
        return merged

    return ExpansionTerms(
        expanded_query=primary.expanded_query or fallback.expanded_query,
        greek_terms=_merge_model_lists(primary.greek_terms, fallback.greek_terms, keys=("greek", "transliteration"))[:8],
        latin_terms=_merge_model_lists(primary.latin_terms, fallback.latin_terms, keys=("latin",))[:8],
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
    return state.query_type == QueryType.SPECIFIC_ENTITY or state.complexity == QueryComplexity.SIMPLE


async def _get_embedding(_deps: Deps, text: str) -> list[float]:
    """Get embedding via Gemini embedding API."""
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY required for embeddings")

    genai.configure(api_key=api_key)

    def _embed() -> list[float]:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]

    return await asyncio.to_thread(_embed)


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
    return Evidence(
        id=node_id,
        label=node.get("label", node_id),
        type=node.get("type", ""),
        layer=layer,
        source=source,
        description=node.get("description", ""),
        score=score,
        period=node.get("period"),
        school=node.get("school"),
        role=node.get("role"),
        metadata=node.get("metadata", {}) or {},
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
            score += _overlap_score(title, ev.author, ev.description, ev.text_content) * 12
            if ev.author and any(hint in ev.author.lower() for hint in author_hints):
                score += 18
            if ev.school and school_hints and any(hint in ev.school.lower() for hint in school_hints):
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

    ordered = sorted(scored_titles.values(), key=lambda item: (-item[1], item[0].lower()))
    return [title for title, _ in ordered]


async def _fetch_passages_for_nodes(
    deps: Deps,
    node_ids: list[str],
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch passages linked to nodes via passage_citations."""
    if not node_ids:
        return []
    placeholders = ", ".join(f"${i + 1}" for i in range(len(node_ids)))
    limit_clause = f"LIMIT {limit}" if limit is not None else ""
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
        ORDER BY pc.confidence DESC, p.sequence_number
        {limit_clause}
        """,
        *node_ids,
    )
    return rows


async def _fetch_translation_for_passage(
    deps: Deps,
    passage_id: str,
) -> dict[str, Any] | None:
    """Find an English translation passage linked through translation_of edges."""
    if not deps.outgoing_edges and not deps.incoming_edges:
        return None

    rows = await deps.db.fetch(
        f"""
        SELECT kg_node_id
        FROM {DB_SCHEMA}.passage_citations
        WHERE passage_id = $1
        """,
        passage_id,
    )
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
        metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
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
        if not text:
            continue
        metadata = node.get("metadata") if isinstance(node.get("metadata"), dict) else {}
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
            "sequence_number": ev.metadata.get("sequence_number") if isinstance(ev.metadata, dict) else None,
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
    candidates = [bundle for bundle in candidates if bundle.bundle_id not in seen_bundle_ids]
    if not candidates:
        return []

    candidates.sort(key=lambda bundle: _bundle_score(bundle, state), reverse=True)
    target = min(remaining, max(4, min(16, budget_limit // 2)))
    selected = candidates[:target]
    for bundle in selected:
        if bundle.language in {"grc", "lat"}:
            translation = await _fetch_translation_for_passage(ctx.deps, bundle.original_passage_id)
            if translation and translation.get("text_content"):
                bundle.translation_text = translation.get("text_content")
                bundle.translation_passage_id = (
                    str(translation["passage_id"])
                    if translation.get("passage_id")
                    else None
                )
                bundle.token_estimate = RetrievalBudget.estimate_tokens(
                    "\n".join(part for part in (bundle.original_text, bundle.translation_text) if part)
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
    non_passage = {item.id: item for item in state.all_evidence() if item.type != "passage"}
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
        fuzzy_candidates = node_aliases if preferred_support == "metadata" else bundle_aliases
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


def _bundle_score(bundle: EvidenceBundle, state: RAGState) -> tuple[int, int, int]:
    query_score = _bundle_query_score(bundle, state)
    features = _bundle_academic_features(bundle, state)
    source_weight = 2 if bundle.source == EvidenceSource.TREE_REASONING else 1
    evidence_weight = {
        "direct_text": 3,
        "ancient_testimony": 2,
        "counter_evidence": 1,
    }.get(features["evidence_class"], 1)
    return (query_score, evidence_weight + source_weight, -bundle.token_estimate)


def _build_context_pack(state: RAGState) -> ContextPack:
    """Pack KG metadata, section summaries, and bundles into a long context."""
    budget = state.retrieval_budget
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
        if sum(budget.estimate_tokens(item) for item in pack.kg_metadata) + line_tokens > kg_budget:
            continue
        pack.kg_metadata.append(line)
        pack.node_refs[ev.id] = str(node_idx)
        node_idx += 1

    section_budget = budget.layer_budget("section_summaries")
    selected_sections = state.metadata.get("selected_sections", [])
    for section in selected_sections:
        line = _section_line(section)
        line_tokens = budget.estimate_tokens(line)
        if sum(budget.estimate_tokens(item) for item in pack.section_summaries) + line_tokens > section_budget:
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
        scored_bundles = [
            item for item in scored_bundles if item[0][0] > 0
        ]
    prioritized_pairs: list[tuple[tuple[int, int, int], EvidenceBundle]] = []
    overflow_pairs: list[tuple[tuple[int, int, int], EvidenceBundle]] = []
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

    parts: list[str] = []
    if pack.kg_metadata:
        parts.append("## KG Metadata\n" + "\n".join(pack.kg_metadata))
    if pack.section_summaries:
        parts.append("## Work Sections\n" + "\n".join(pack.section_summaries))
    if pack.passage_bundles:
        bundle_lines = []
        for bundle in pack.passage_bundles:
            ref = pack.bundle_refs[bundle.bundle_id]
            lines = [
                f"[{ref}] {_bundle_label(bundle)}",
                f"Section: {bundle.section_path or 'unknown'}",
                f'Original: "{truncate_text(bundle.original_text, 1600)}"',
            ]
            if bundle.translation_text:
                lines.append(f'Translation: "{truncate_text(bundle.translation_text, 1600)}"')
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
            "top_bundle_rankings": _top_bundle_debug_entries(scored_bundles, pack.bundle_refs, state),
        },
    )
    return pack


def _reverse_ref_maps(state: RAGState) -> tuple[dict[str, EvidenceBundle], dict[str, Evidence]]:
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


def _render_answer_fallback(state: RAGState) -> str:
    """Deterministic fallback answer that is guaranteed to stay grounded."""
    lines: list[str] = []
    claims_by_facet: dict[str, list[ClaimLedgerItem]] = {}
    for item in state.claim_ledger:
        claims_by_facet.setdefault(item.facet_id or "_general", []).append(item)

    supported_claims = [
        item
        for item in state.claim_ledger
        if item.status == ClaimStatus.SUPPORTED and _claim_reference_markers(state, item)
    ]
    if supported_claims:
        intro_item = supported_claims[0]
        intro_refs = " ".join(_claim_reference_markers(state, intro_item))
        intro_line = intro_item.claim.rstrip(".")
        if state.insufficient_evidence:
            intro_line = f"Available evidence is partial, but the best-supported result is this: {intro_line}"
        lines.append(f"{intro_line}. {intro_refs}".replace("..", "."))

    if state.scholarly_dossier.facets:
        for facet in state.scholarly_dossier.facets[:4]:
            facet_claims = claims_by_facet.get(facet.facet_id, [])
            if not facet_claims:
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
                    body_parts.append(f"{item.claim.rstrip('.')} {' '.join(refs)}")
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
                        lines.append(f'> Original: "{quote_item.quote_original}" {" ".join(refs)}')
                    if quote_item.quote_translation:
                        lines.append(f'> Translation: "{quote_item.quote_translation}" {" ".join(refs)}')
        if state.scholarly_dossier.insufficiency_notes:
            note_refs = _claim_reference_markers(state, supported_claims[0]) if supported_claims else []
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
            lines.append(f"{item.claim.rstrip('.')} {' '.join(refs)}")
            if item.quote_original:
                lines.append(
                    f'> Original: "{item.quote_original}" {" ".join(refs)}'
                )
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
            lines.append(f"{item.claim.rstrip('.')} {' '.join(refs)}")
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
    quote_request = _question_requests_quote(state) or _question_requests_original(state) or _question_requests_translation(state)
    insufficient = state.insufficient_evidence or all_insufficient or (quote_request and not supported_passage_claim)
    state.insufficient_evidence = insufficient
    if insufficient:
        state.metadata["insufficient_evidence"] = True


def _render_evidence_packet(state: RAGState) -> list[dict[str, Any]]:
    """Compact selected evidence for the final prose pass."""
    packet: list[dict[str, Any]] = []
    seen: set[str] = set()
    evidence_by_id = {
        ev.id: ev for ev in state.all_evidence() if ev.type != "passage"
    }
    bundles_by_id = {bundle.bundle_id: bundle for bundle in state.context_pack.passage_bundles}

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
                    "evidence_class": _bundle_academic_features(bundle, state)["evidence_class"],
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
                    "description": truncate_text(ev.description or ev.text_content or "", 420),
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
                        "description": truncate_text(ev.description or ev.text_content or "", 420),
                        "period": ev.period,
                        "school": ev.school,
                    }
                )
    return packet


def _select_direct_quote_bundle(state: RAGState) -> EvidenceBundle | None:
    """Pick the best exact bundle for philological quote requests."""
    if not (_question_requests_quote(state) or _question_requests_original(state) or _question_requests_translation(state)):
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
        label_haystack = " ".join(part for part in (bundle.author, bundle.work_title, bundle.canonical_ref) if part).lower()
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


def _heuristic_claim_ledger_acceptable(state: RAGState, claims: list[ClaimLedgerItem]) -> bool:
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
    has_metadata = any(item.support_type == "metadata" and item.evidence_ids for item in claims)
    has_passage = any(item.support_type == "passage" and item.evidence_ids for item in claims)
    if state.query_type == QueryType.SPECIFIC_ENTITY:
        return has_metadata and has_passage
    return has_passage and (has_metadata or len(covered_facets) >= 2 or len(claims) >= 6)


def _dedupe_claims(claims: list[ClaimLedgerItem], *, limit: int = 12) -> list[ClaimLedgerItem]:
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
    dossier = state.scholarly_dossier if state.scholarly_dossier.facets else _build_scholarly_dossier(state)
    return [
        facet
        for facet in dossier.facets
        if facet.primary_bundle_ids or facet.testimony_bundle_ids or facet.metadata_ids
    ]


def _render_requirements(state: RAGState) -> dict[str, int]:
    supported_facets = _supported_dossier_facets(state)
    quoted_claims = sum(
        1
        for item in state.claim_ledger
        if item.quote_original or item.quote_translation
    )
    required_sections = 0
    if len(supported_facets) >= 2:
        required_sections = min(4, len(supported_facets))
    elif supported_facets:
        required_sections = 1

    required_quote_blocks = 0
    if quoted_claims:
        required_quote_blocks = 1
        if quoted_claims >= 4 and len(supported_facets) >= 3:
            required_quote_blocks = 2

    min_chars = 300
    if supported_facets:
        min_chars += 180 * min(4, len(supported_facets))
    if quoted_claims:
        min_chars += 120 * min(2, quoted_claims)
    if state.insufficient_evidence:
        min_chars = max(300, min_chars - 180)

    return {
        "required_sections": required_sections,
        "required_quote_blocks": required_quote_blocks,
        "min_chars": min_chars,
    }


def _answer_shape_metrics(answer: str) -> dict[str, int]:
    return {
        "chars": len(answer.strip()),
        "section_headers": len(re.findall(r"^#{1,3}\s+", answer, flags=re.MULTILINE)),
        "quote_blocks": len(re.findall(r"^>\s", answer, flags=re.MULTILINE)),
    }


def _answer_is_too_compressed(state: RAGState, answer: str) -> bool:
    if not answer.strip():
        return True
    requirements = _render_requirements(state)
    metrics = _answer_shape_metrics(answer)
    if metrics["chars"] < requirements["min_chars"]:
        return True
    if requirements["required_sections"] and metrics["section_headers"] < requirements["required_sections"]:
        return True
    return bool(
        requirements["required_quote_blocks"]
        and metrics["quote_blocks"] < requirements["required_quote_blocks"]
    )


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
        1
        for item in augmented
        if item.quote_original or item.quote_translation
    )
    required_quotes = _render_requirements(state)["required_quote_blocks"]
    target_claim_count = min(10, max(4, len(required_facets) * 2))

    for item in fallback_claims:
        needs_facet = bool(item.facet_id and item.facet_id in required_facets and item.facet_id not in supported_facets)
        needs_quote = bool(
            quote_claims < required_quotes and (item.quote_original or item.quote_translation)
        )
        needs_density = len(augmented) < target_claim_count and item.support_type == "passage"
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
    dossier = state.scholarly_dossier if state.scholarly_dossier.facets else _build_scholarly_dossier(state)
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
                    status=ClaimStatus.SUPPORTED if summary else ClaimStatus.INSUFFICIENT,
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
                (bundle_lookup[bundle_id] for bundle_id in facet.primary_bundle_ids if bundle_id in bundle_lookup),
                None,
            )
            testimony_bundle = next(
                (bundle_lookup[bundle_id] for bundle_id in facet.testimony_bundle_ids if bundle_id in bundle_lookup),
                None,
            )
            counter_bundle = next(
                (bundle_lookup[bundle_id] for bundle_id in facet.counter_bundle_ids if bundle_id in bundle_lookup),
                None,
            )
            metadata_node = next(
                (node_lookup[node_id] for node_id in facet.metadata_ids if node_id in node_lookup),
                None,
            )
            lead_bundle = primary_bundle or testimony_bundle or counter_bundle
            evidence_ids = list(
                dict.fromkeys(
                    [
                        *(facet.primary_bundle_ids[:2] if facet.primary_bundle_ids else []),
                        *(facet.testimony_bundle_ids[:2] if facet.testimony_bundle_ids else []),
                        *(facet.counter_bundle_ids[:1] if facet.counter_bundle_ids else []),
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
                summary = truncate_text(metadata_node.description or _compact_node_line(metadata_node), 220)
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
                            evidence_class=_bundle_academic_features(lead_bundle, state)["evidence_class"],
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
                    evidence_class=_bundle_academic_features(bundle, state)["evidence_class"],
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
                    status=ClaimStatus.INSUFFICIENT if state.insufficient_evidence else ClaimStatus.SUPPORTED,
                )
            )
    return _dedupe_claims(claims, limit=12)


def _normalize_quote_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip("\"“”")).lower()


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


def _quote_supported_by_refs(
    quote: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
) -> bool:
    normalized_quote = _normalize_quote_text(quote)
    if len(re.sub(r"\W+", "", normalized_quote)) < 6:
        return True
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
    return any(normalized_quote in _normalize_quote_text(text) for text in source_texts)


def _sanitize_line_quotes(
    line: str,
    refs: list[str],
    bundles_by_ref: dict[str, EvidenceBundle],
    nodes_by_ref: dict[str, Evidence],
) -> str | None:
    matches = list(QUOTE_RE.finditer(line))
    if not matches:
        return line

    sanitized = line
    unsupported_found = False
    for match in reversed(matches):
        quote = match.group(1)
        if _quote_supported_by_refs(quote, refs, bundles_by_ref, nodes_by_ref):
            continue
        unsupported_found = True
        sanitized = sanitized[: match.start()] + quote + sanitized[match.end() :]

    sanitized = re.sub(r"\s{2,}", " ", sanitized).strip()
    if unsupported_found and sanitized.lower().startswith(
        ("original:", "translation:", "greek original:", "english translation:", "latin original:")
    ):
        return None
    return sanitized or None


def _is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    return len(stripped) <= 80 and stripped.endswith(":") and stripped.count(" ") <= 8


def _verify_answer_programmatically(state: RAGState, _depth: int = 0) -> tuple[str, list[Citation]]:
    """Keep only grounded lines and emit citations for the surviving refs."""
    bundles_by_ref, nodes_by_ref = _reverse_ref_maps(state)
    valid_refs = set(bundles_by_ref) | set(nodes_by_ref)
    kept_lines: list[str] = []
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
                    block_line, refs, bundles_by_ref, nodes_by_ref
                )
                if not sanitized:
                    continue
                kept_lines.append(_normalize_reference_markers(sanitized, refs))
            seen_refs.update(block_refs)
            continue
        refs = _extract_line_refs(line)
        valid_line_refs = [ref for ref in refs if ref in valid_refs]
        if not valid_line_refs:
            continue
        line = _sanitize_line_quotes(line, valid_line_refs, bundles_by_ref, nodes_by_ref)
        if not line:
            continue
        line = _normalize_reference_markers(line, valid_line_refs)
        _flush_pending_structure()
        kept_lines.append(line)
        seen_refs.update(valid_line_refs)

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
                    verification_note="Programmatically verified from evidence bundle",
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
                    verification_note="Programmatically verified from packed metadata",
                )
            )

    return "\n".join(kept_lines), citations


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


async def _discover_corpus(ctx: GraphRunContext[RAGState, Deps]) -> None:
    """Shared discovery step used by the active pipeline."""
    state = ctx.state
    budget = state.retrieval_budget
    queries = _search_queries(state)
    trace_payload: dict[str, Any] = {
        "queries": queries,
        "semantic_hits": [],
        "seed_node_ids": [],
        "passage_anchor_ids": [],
        "linked_passages": [],
    }
    if not queries:
        _trace_stage(state, "discover_corpus", trace_payload)
        return

    limit_per_query = max(8, budget.node_search_limit() // max(1, len(queries)))
    hit_map: dict[str, dict[str, Any]] = {}
    for query in queries:
        try:
            embedding = await _get_embedding(ctx.deps, query)
            hits = await ctx.deps.qdrant.search_nodes(embedding, limit=limit_per_query)
        except Exception:
            logger.warning("Corpus discovery failed for query %s", query)
            continue

        for hit in hits:
            node_id = hit.get("id")
            if not node_id or node_id not in ctx.deps.node_lookup:
                continue
            best = hit_map.get(node_id)
            if best is None or hit.get("score", 0.0) > best.get("score", 0.0):
                hit_map[node_id] = hit

    ordered_hits = sorted(hit_map.values(), key=lambda item: item.get("score", 0.0), reverse=True)
    trace_payload["semantic_hits"] = [
        {
            "id": str(hit.get("id")),
            "score": round(float(hit.get("score", 0.0)), 4),
            "label": ctx.deps.node_lookup.get(str(hit.get("id")), {}).get("label"),
            "type": ctx.deps.node_lookup.get(str(hit.get("id")), {}).get("type"),
        }
        for hit in ordered_hits[:12]
    ]
    _record_tool_call(
        state,
        tool_name="search_entities",
        stage_id="discover_corpus",
        query=" | ".join(queries[:4]),
        rationale="semantic discovery over KG nodes",
        selected_ids=[str(hit.get("id")) for hit in ordered_hits[:12] if hit.get("id")],
        details={
            "queries": queries[:8],
            "hit_count": len(ordered_hits),
        },
    )
    seed_ids: list[str] = []
    passage_anchor_ids: list[str] = []
    existing = state.all_node_ids()
    for hit in ordered_hits:
        node_id = str(hit["id"])
        if node_id in existing:
            continue
        evidence = _make_evidence_from_node(
            node_id,
            ctx.deps.node_lookup[node_id],
            score=hit.get("score", 0.0),
            source=EvidenceSource.SEMANTIC_SEARCH,
        )
        if evidence.layer == EvidenceLayer.PRIMARY:
            state.primary_evidence.append(evidence)
        else:
            state.secondary_evidence.append(evidence)
        existing.add(node_id)
        seed_ids.append(node_id)
        if (
            evidence.layer == EvidenceLayer.PRIMARY
            and evidence.type.lower() != "passage"
            and len(passage_anchor_ids) < 12
        ):
            passage_anchor_ids.append(node_id)

    state.seed_node_ids = list(dict.fromkeys(state.seed_node_ids + seed_ids))
    trace_payload["seed_node_ids"] = state.seed_node_ids[:20]
    if seed_ids:
        _record_reading_decision(
            state,
            stage_id="discover_corpus",
            decision_type="seed_selection",
            title="Select high-value seed nodes",
            rationale="Highest scoring semantic hits become the starting corpus map.",
            selected_ids=seed_ids[:20],
        )

    traversal_limit = state.retrieval_budget.traversal_node_limit()
    try:
        if ctx.deps.traversal and state.seed_node_ids:
            expanded_ids = ctx.deps.traversal.expand(
                seed_ids=state.seed_node_ids,
                max_nodes=traversal_limit,
                score_threshold=0.03,
            )
        else:
            expanded_ids = _expand_graph(
                ctx.deps,
                state.seed_node_ids,
                depth=2,
                max_nodes=traversal_limit,
            )
    except Exception:
        expanded_ids = _expand_graph(
            ctx.deps,
            state.seed_node_ids,
            depth=2,
            max_nodes=traversal_limit,
        )

    _record_tool_call(
        state,
        tool_name="expand_graph_context",
        stage_id="discover_corpus",
        rationale="expand immediate KG neighborhood around seed nodes",
        selected_ids=list(expanded_ids)[:20],
        details={
            "seed_count": len(state.seed_node_ids),
            "expanded_count": len(expanded_ids),
            "traversal_limit": traversal_limit,
        },
    )

    for node_id in expanded_ids:
        if node_id in existing or node_id not in ctx.deps.node_lookup:
            continue
        evidence = _make_evidence_from_node(
            node_id,
            ctx.deps.node_lookup[node_id],
            source=EvidenceSource.GRAPH_TRAVERSAL,
        )
        if evidence.layer == EvidenceLayer.PRIMARY:
            state.primary_evidence.append(evidence)
        else:
            state.secondary_evidence.append(evidence)
        existing.add(node_id)

    state.context_node_ids = list(existing)

    if not passage_anchor_ids:
        passage_anchor_ids = state.seed_node_ids[:12]
    if not passage_anchor_ids:
        passage_anchor_ids = state.context_node_ids[:8]
    state.metadata["passage_anchor_ids"] = passage_anchor_ids
    trace_payload["passage_anchor_ids"] = passage_anchor_ids
    if passage_anchor_ids:
        _record_reading_decision(
            state,
            stage_id="discover_corpus",
            decision_type="passage_anchor_selection",
            title="Choose passage anchors",
            rationale="Prefer primary non-passage nodes to fetch linked textual evidence.",
            selected_ids=passage_anchor_ids[:12],
        )

    try:
        linked_passages = await _fetch_passages_for_nodes(
            ctx.deps,
            passage_anchor_ids,
            limit=max(10, min(60, state.retrieval_budget.passage_bundle_limit() // 3)),
        )
    except Exception:
        linked_passages = []

    _record_tool_call(
        state,
        tool_name="read_linked_passages",
        stage_id="discover_corpus",
        rationale="fetch passages linked to the strongest anchor nodes",
        selected_ids=[str(row.get("passage_id")) for row in linked_passages[:16] if row.get("passage_id")],
        details={
            "anchor_ids": passage_anchor_ids[:12],
            "linked_count": len(linked_passages),
        },
    )

    for row in linked_passages:
        pid = str(row["passage_id"])
        if pid in existing:
            continue
        state.primary_evidence.append(
            Evidence(
                id=pid,
                label=f"{row['author']}, {row['title']} {row['canonical_ref'] or ''}".strip(),
                type="passage",
                layer=EvidenceLayer.PRIMARY,
                source=EvidenceSource.PASSAGE_CITATION,
                description=truncate_text(row.get("text_content", ""), 700),
                passage_id=pid,
                canonical_ref=row.get("canonical_ref"),
                author=row.get("author"),
                work_id=row.get("work_id"),
                work_title=row.get("title"),
                text_content=row.get("text_content"),
                confidence=row.get("confidence"),
                language=row.get("language"),
            )
        )
        existing.add(pid)

    state.passages_used = len([ev for ev in state.primary_evidence if ev.type == "passage"])
    state.accumulated_context = _build_context_from_evidence(state.all_evidence())
    trace_payload["linked_passages"] = [
        {
            "passage_id": str(row["passage_id"]),
            "title": row.get("title"),
            "author": row.get("author"),
            "canonical_ref": row.get("canonical_ref"),
            "language": row.get("language"),
            "confidence": row.get("confidence"),
        }
        for row in linked_passages[:12]
    ]
    _trace_stage(state, "discover_corpus", trace_payload)


def _ensure_notebook(state: RAGState) -> ResearchNotebook:
    if not state.research_notebook:
        state.research_notebook = ResearchNotebook()
    return state.research_notebook


def _record_tool_call(
    state: RAGState,
    *,
    tool_name: str,
    stage_id: str,
    status: str = "complete",
    query: str | None = None,
    rationale: str | None = None,
    work_id: str | None = None,
    work_title: str | None = None,
    section_path: str | None = None,
    selected_ids: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    notebook = _ensure_notebook(state)
    resolved_ids = list(selected_ids or [])
    notebook.tool_calls.append(
        ResearchToolCall(
            tool_call_id=f"{stage_id}:{tool_name}:{len(notebook.tool_calls) + 1}",
            tool_name=tool_name,
            stage_id=stage_id,
            status=status,
            query=query,
            rationale=rationale,
            work_id=work_id,
            work_title=work_title,
            section_path=section_path,
            selected_ids=resolved_ids,
            detail_count=len(resolved_ids),
            details=details or {},
        )
    )


def _record_reading_decision(
    state: RAGState,
    *,
    stage_id: str,
    decision_type: str,
    title: str,
    rationale: str = "",
    facet_id: str | None = None,
    selected_ids: list[str] | None = None,
    rejected_ids: list[str] | None = None,
    supporting_refs: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    notebook = _ensure_notebook(state)
    notebook.reading_decisions.append(
        ReadingDecision(
            decision_id=f"{stage_id}:{decision_type}:{len(notebook.reading_decisions) + 1}",
            stage_id=stage_id,
            decision_type=decision_type,
            title=title,
            rationale=rationale,
            facet_id=facet_id,
            selected_ids=list(selected_ids or []),
            rejected_ids=list(rejected_ids or []),
            supporting_refs=list(supporting_refs or []),
            metadata=metadata or {},
        )
    )


def _selected_section_summary(node: Any, work_id: str, parent_path: str = "") -> list[dict[str, Any]]:
    """Flatten a tree node recursively into section summary dicts."""
    current_path = f"{parent_path} > {node.title}" if parent_path else node.title
    result = [{
        "work_id": work_id,
        "node_id": node.node_id,
        "title": node.title,
        "path": getattr(node, "path", None) or current_path,
        "summary": node.summary,
        "abstract": getattr(node, "abstract", None) or node.summary,
        "canonical_refs": getattr(node, "canonical_refs", []) or [],
        "translation_available": getattr(node, "translation_available", False),
        "quote_density": getattr(node, "quote_density", 0.0),
        "token_estimate": getattr(node, "token_estimate", 0),
        "start_passage": node.start_passage,
        "end_passage": node.end_passage,
    }]
    for child in node.nodes:
        result.extend(_selected_section_summary(child, work_id, current_path))
    return result


def _heuristic_select_sections(question: str, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_terms = {
        token
        for token in re.findall(r"[A-Za-zÀ-ÿἀ-῾]+", question.lower())
        if len(token) > 3
    }
    scored: list[tuple[int, dict[str, Any]]] = []
    for section in sections:
        haystack = " ".join(
            str(section.get(key, "")).lower()
            for key in ("title", "summary", "abstract", "path")
        )
        score = sum(1 for term in query_terms if term in haystack)
        if score or not query_terms:
            scored.append((score, section))
    if not scored:
        return sections[: min(6, len(sections))]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [section for _, section in scored[: min(8, len(scored))]]


async def _navigate_sections_with_llm(
    ctx: GraphRunContext[RAGState, Deps],
    *,
    question: str,
    work_title: str,
    author: str,
    work_id: str,
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload = [
        {
            "work_id": work_id,
            "node_id": section["node_id"],
            "title": section["title"],
            "path": section["path"],
            "summary": section["summary"],
            "abstract": section.get("abstract", ""),
            "canonical_refs": section.get("canonical_refs", []),
        }
        for section in sections
    ]
    prompt = TREE_NAVIGATION_PROMPT.format(
        question=question,
        work_title=work_title,
        author=author,
        sections_json=truncate_json(payload, 12000),
    )
    try:
        raw = await ctx.deps.llm.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=1200,
            thinking_mode=True,
            cache_key=f"tree-nav::{work_id}",
            cache_prefix="tree_navigation_v1",
        )
        parsed = TreeNavigationResult.model_validate(_parse_json(raw))
        selected_ids = {item.node_id for item in parsed.selected_nodes}
        selected = [section for section in sections if section["node_id"] in selected_ids]
        return selected or _heuristic_select_sections(question, sections)
    except Exception:
        return _heuristic_select_sections(question, sections)


async def _build_research_frame(ctx: GraphRunContext[RAGState, Deps]) -> None:
    state = ctx.state
    notebook = _ensure_notebook(state)
    if notebook.question_frame:
        notebook.facets = _normalize_notebook_facets(state, notebook.facets)
        return

    corpus_scope = "\n".join(sorted({ev.label for ev in state.all_evidence() if ev.label})[:20])
    if _should_minimize_llm_calls(state):
        notebook.question_frame = state.question
        notebook.facets = _default_research_facets(state)
        if not state.sub_queries:
            state.sub_queries = [state.question]
        if not notebook.competing_hypotheses:
            notebook.competing_hypotheses = [
                f"The main answer is textually well supported for: {state.question}",
                f"The evidence is more fragmented or interpretive for: {state.question}",
            ]
        notebook.open_questions = state.sub_queries[:3]
    else:
        try:
            raw = await ctx.deps.llm.generate(
                FRAME_RESEARCH_PROMPT.format(
                    question=state.question,
                    corpus_scope=corpus_scope or "(none)",
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=800,
                thinking_mode=True,
                cache_key="research-frame",
                cache_prefix="research_frame_v1",
            )
            framed = ResearchFrame.model_validate(_parse_json(raw))
            notebook.question_frame = framed.question_frame
            notebook.facets = _normalize_notebook_facets(state, framed.facets)
            notebook.open_questions = framed.open_questions[:5]
            notebook.competing_hypotheses = framed.competing_hypotheses[:4]
            if framed.sub_questions:
                state.sub_queries = framed.sub_questions[:4]
        except Exception:
            notebook.question_frame = state.question
            notebook.facets = _default_research_facets(state)
            if not state.sub_queries:
                state.sub_queries = [state.question]
            if not notebook.competing_hypotheses:
                notebook.competing_hypotheses = [
                    f"The main answer is textually well supported for: {state.question}",
                    f"The evidence is more fragmented or interpretive for: {state.question}",
                ]
            notebook.open_questions = state.sub_queries[:3]

    if not notebook.facets:
        notebook.facets = _default_research_facets(state)
    notebook.corpus_scope = sorted({ev.label for ev in state.all_evidence() if ev.label})[:40]
    notebook.work_priorities = _candidate_work_titles(state)[: state.retrieval_budget.candidate_work_limit()]
    _record_reading_decision(
        state,
        stage_id="research_notebook",
        decision_type="facet_plan",
        title="Plan scholarly reading facets",
        rationale="The notebook frames the question into research facets before hierarchical reading.",
        selected_ids=[facet.facet_id for facet in notebook.facets[:8]],
        metadata={
            "question_frame": notebook.question_frame,
            "work_priorities": notebook.work_priorities[:12],
        },
    )
    _build_scholarly_dossier(state)
    _trace_stage(
        state,
        "research_notebook",
        {
            "question_frame": notebook.question_frame,
            "facets": [
                {
                    "facet_id": facet.facet_id,
                    "title": facet.title,
                    "priority": facet.priority,
                    "required_support": facet.required_support,
                }
                for facet in notebook.facets
            ],
            "sub_queries": state.sub_queries[:8],
            "competing_hypotheses": notebook.competing_hypotheses[:6],
            "work_priorities": notebook.work_priorities[:12],
        },
    )


async def _plan_reading(ctx: GraphRunContext[RAGState, Deps]) -> None:
    state = ctx.state
    notebook = _ensure_notebook(state)
    candidate_titles = notebook.work_priorities[: state.retrieval_budget.candidate_work_limit()]
    planned_work_titles = candidate_titles
    planned_facet_ids = [facet.facet_id for facet in notebook.facets[:4]]
    rationale = "heuristic reading plan"
    mode = "heuristic"

    if candidate_titles and not _should_minimize_llm_calls(state):
        try:
            raw = await ctx.deps.llm.generate(
                READING_PLAN_PROMPT.format(
                    question_frame=notebook.question_frame or state.question,
                    work_titles="\n".join(f"- {title}" for title in candidate_titles[:12]),
                    facets_json=truncate_json(
                        [
                            {
                                "facet_id": facet.facet_id,
                                "title": facet.title,
                                "question": facet.question,
                                "priority": facet.priority,
                            }
                            for facet in notebook.facets[:8]
                        ],
                        6000,
                    ),
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=700,
                thinking_mode=True,
                cache_key="reading-plan",
                cache_prefix="reading_plan_v1",
            )
            parsed = ReadingPlanResult.model_validate(_parse_json(raw))
            normalized_titles = [title for title in parsed.work_titles if title in candidate_titles]
            if normalized_titles:
                planned_work_titles = normalized_titles + [
                    title for title in candidate_titles if title not in normalized_titles
                ]
            normalized_facets = [
                facet_id
                for facet_id in parsed.facet_ids
                if any(facet.facet_id == facet_id for facet in notebook.facets)
            ]
            if normalized_facets:
                planned_facet_ids = normalized_facets
            rationale = parsed.rationale or rationale
            mode = "llm"
        except Exception:
            mode = "heuristic"

    planned_work_titles = planned_work_titles[: state.retrieval_budget.candidate_work_limit()]
    planned_facet_ids = planned_facet_ids[: min(6, len(planned_facet_ids))]
    state.metadata["planned_work_titles"] = planned_work_titles
    state.metadata["planned_facet_ids"] = planned_facet_ids
    notebook.work_priorities = planned_work_titles
    if planned_facet_ids:
        facet_by_id = {facet.facet_id: facet for facet in notebook.facets}
        notebook.facets = [
            facet_by_id[facet_id]
            for facet_id in planned_facet_ids
            if facet_id in facet_by_id
        ] + [
            facet
            for facet in notebook.facets
            if facet.facet_id not in set(planned_facet_ids)
        ]
    _record_tool_call(
        state,
        tool_name="plan_reading",
        stage_id="reading_plan",
        status=mode,
        query=notebook.question_frame or state.question,
        rationale=rationale,
        selected_ids=planned_work_titles[:12],
        details={"planned_facet_ids": planned_facet_ids[:8]},
    )
    _record_reading_decision(
        state,
        stage_id="reading_plan",
        decision_type="reading_order",
        title="Prioritize works and facets before hierarchical reading",
        rationale=rationale,
        selected_ids=planned_work_titles[:12],
        metadata={"planned_facet_ids": planned_facet_ids[:8]},
    )
    _trace_stage(
        state,
        "reading_plan",
        {
            "mode": mode,
            "planned_work_titles": planned_work_titles[:12],
            "planned_facet_ids": planned_facet_ids[:8],
            "rationale": rationale,
        },
    )


@dataclass
class ClassifyComplexity(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Legacy compatibility node delegating to query-type classification."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandQuery:
        return await ClassifyQueryType().run(ctx)


@dataclass
class ClassifyQueryType(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Classify query type and initialize pipeline config and budgets."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandQuery:
        state = ctx.state
        heuristic_query_type = _default_query_type(state.question)
        if heuristic_query_type == QueryType.SPECIFIC_ENTITY:
            query_type = heuristic_query_type
            confidence = 0.75
            reason = "deterministic heuristic"
        else:
            try:
                raw = await ctx.deps.llm.generate(
                    CLASSIFY_QUERY_TYPE_PROMPT.format(question=state.question),
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.0,
                    max_tokens=256,
                    cache_key="query-classifier",
                    cache_prefix="query_classifier_v1",
                )
                parsed = ClassificationResult.model_validate(_parse_json(raw))
                query_type = parsed.query_type
                confidence = parsed.confidence
                reason = parsed.reason
            except Exception:
                query_type = heuristic_query_type
                confidence = 0.45
                reason = "heuristic fallback"

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


@dataclass
class ExpandQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Expand the query and seed philological metadata."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DiscoverCorpus:
        state = ctx.state
        fallback_expansion = _default_expansion(state.question)
        if not state.pipeline_config.use_expansion or _should_minimize_llm_calls(state):
            state.expanded_query = state.question
            state.expansion_terms = fallback_expansion
            state.metadata["expanded_query"] = state.expanded_query
            _trace_stage(
                state,
                "expand_query",
                {
                    "mode": "heuristic",
                    "expanded_query": state.expanded_query,
                    "philosophers": fallback_expansion.philosophers[:8],
                    "concepts": fallback_expansion.concepts[:8],
                    "schools": fallback_expansion.schools[:8],
                    "periods": fallback_expansion.periods[:6],
                },
            )
            return DiscoverCorpus()

        mode = "llm"
        try:
            raw = await ctx.deps.llm.generate(
                EXPAND_QUERY_PROMPT.format(question=state.question),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=800,
                cache_key="query-expansion",
                cache_prefix="query_expansion_v1",
            )
            expansion = _merge_expansion_terms(
                ExpansionTerms.model_validate(_parse_json(raw)),
                fallback_expansion,
            )
        except Exception:
            expansion = fallback_expansion
            mode = "fallback"

        state.expansion_terms = expansion
        state.expanded_query = expansion.expanded_query or state.question
        state.metadata["expanded_query"] = state.expanded_query
        _trace_stage(
            state,
            "expand_query",
            {
                "mode": mode,
                "expanded_query": state.expanded_query,
                "philosophers": expansion.philosophers[:8],
                "concepts": expansion.concepts[:8],
                "schools": expansion.schools[:8],
                "periods": expansion.periods[:6],
            },
        )
        return DiscoverCorpus()


@dataclass
class DiscoverCorpus(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Broad discovery over KG nodes and linked passages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> BuildResearchNotebook:
        await _discover_corpus(ctx)
        return BuildResearchNotebook()


@dataclass
class BuildResearchNotebook(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Create the explicit notebook used by later reasoning stages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> PlanReading:
        await _build_research_frame(ctx)
        return PlanReading()


@dataclass
class PlanReading(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Plan work/facet reading order before tree navigation."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeNavigateWorks:
        await _plan_reading(ctx)
        return TreeNavigateWorks()


@dataclass
class TreeNavigateWorks(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Navigate work trees recursively before loading many passages."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ExpandEvidenceBundles:
        state = ctx.state
        state.metadata["selected_sections"] = []

        if not ctx.deps.tree_index or not state.pipeline_config.use_tree_reasoning:
            _trace_stage(
                state,
                "tree_navigation",
                {
                    "mode": "skipped",
                    "reason": "tree reasoning unavailable"
                    if not ctx.deps.tree_index
                    else "tree reasoning disabled by config",
                    "candidate_work_titles": state.research_notebook.work_priorities[
                        : state.retrieval_budget.candidate_work_limit()
                    ],
                    "selected_sections": [],
                },
            )
            return ExpandEvidenceBundles()

        work_titles = _candidate_work_titles(state)
        if not work_titles:
            return ExpandEvidenceBundles()
        _record_tool_call(
            state,
            tool_name="search_works",
            stage_id="tree_navigation",
            query=state.research_notebook.question_frame or state.question,
            rationale="prioritize works before opening hierarchical indices",
            selected_ids=work_titles[: state.retrieval_budget.candidate_work_limit()],
            details={"candidate_count": len(work_titles)},
        )

        try:
            work_ids = await ctx.deps.tree_index.resolve_work_ids(work_titles[: state.retrieval_budget.candidate_work_limit()])
            indices = await ctx.deps.tree_index.load_indices(work_ids[: state.retrieval_budget.candidate_work_limit()])
        except Exception:
            logger.warning("Tree navigation unavailable")
            return ExpandEvidenceBundles()

        selected_sections: list[dict[str, Any]] = []
        for index in indices:
            _record_tool_call(
                state,
                tool_name="open_work_tree",
                stage_id="tree_navigation",
                rationale="inspect the hierarchical section index before reading passages",
                work_id=index.work_id,
                work_title=index.title,
                selected_ids=[node.node_id for node in index.nodes[:12]],
                details={
                    "root_node_count": len(index.nodes),
                    "author": index.author,
                },
            )
            flat_sections: list[dict[str, Any]] = []
            for node in index.nodes:
                flat_sections.extend(_selected_section_summary(node, index.work_id))
            if not flat_sections:
                continue

            top_sections = flat_sections[: state.retrieval_budget.section_summary_limit()]
            if _should_minimize_llm_calls(state):
                chosen = _heuristic_select_sections(
                    state.research_notebook.question_frame or state.question,
                    top_sections,
                )
                section_mode = "heuristic"
            else:
                chosen = await _navigate_sections_with_llm(
                    ctx,
                    question=state.research_notebook.question_frame or state.question,
                    work_title=index.title,
                    author=index.author,
                    work_id=index.work_id,
                    sections=top_sections,
                )
                section_mode = "llm"
            selected_sections.extend(chosen)
            _record_tool_call(
                state,
                tool_name="select_work_sections",
                stage_id="tree_navigation",
                status=section_mode,
                rationale="choose the most promising sections before expanding into passages",
                work_id=index.work_id,
                work_title=index.title,
                selected_ids=[section["node_id"] for section in chosen[:12]],
                details={
                    "candidate_sections": len(top_sections),
                    "selected_count": len(chosen),
                },
            )
            if chosen:
                _record_reading_decision(
                    state,
                    stage_id="tree_navigation",
                    decision_type="section_selection",
                    title=f"Select sections in {index.title}",
                    rationale="Prioritize sections whose summaries best cover the framed research facets.",
                    selected_ids=[section["node_id"] for section in chosen[:12]],
                    rejected_ids=[
                        section["node_id"]
                        for section in top_sections
                        if section["node_id"] not in {item["node_id"] for item in chosen}
                    ][:12],
                    metadata={
                        "work_id": index.work_id,
                        "work_title": index.title,
                        "paths": [section.get("path") for section in chosen[:8]],
                    },
                )

        state.metadata["selected_sections"] = selected_sections
        state.research_notebook.work_priorities = work_titles[: state.retrieval_budget.candidate_work_limit()]
        _trace_stage(
            state,
            "tree_navigation",
            {
                "candidate_work_titles": work_titles[: state.retrieval_budget.candidate_work_limit()],
                "selected_sections": [
                    {
                        "work_id": section["work_id"],
                        "node_id": section["node_id"],
                        "path": section.get("path"),
                        "title": section.get("title"),
                    }
                    for section in selected_sections[:20]
                ],
            },
        )
        return ExpandEvidenceBundles()


@dataclass
class ExpandEvidenceBundles(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Load passages for selected sections and pair translations when possible."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SeekCounterEvidence:
        state = ctx.state
        bundles: list[EvidenceBundle] = []
        seen_bundle_ids = state.bundle_ids()
        selected_sections = state.metadata.get("selected_sections", [])
        translation_pairs: list[dict[str, Any]] = []

        if ctx.deps.tree_index and selected_sections:
            work_ids = {section["work_id"] for section in selected_sections}
            indices = await ctx.deps.tree_index.load_indices(list(work_ids))
            indices_by_id = {index.work_id: index for index in indices}

            for section in selected_sections:
                index = indices_by_id.get(section["work_id"])
                if not index:
                    continue
                try:
                    rows = await ctx.deps.tree_index.extract_passages(
                        index,
                        [section["node_id"]],
                        limit=max(4, min(40, state.retrieval_budget.passage_bundle_limit() // max(1, len(selected_sections)))),
                    )
                except Exception:
                    continue
                _record_tool_call(
                    state,
                    tool_name="read_section",
                    stage_id="evidence_bundles",
                    rationale="expand the selected section into concrete passage bundles",
                    work_id=index.work_id,
                    work_title=index.title,
                    section_path=section.get("path"),
                    selected_ids=[str(row.get("passage_id")) for row in rows[:16] if row.get("passage_id")],
                    details={
                        "node_id": section["node_id"],
                        "selected_count": len(rows),
                    },
                )

                for row in rows:
                    bundle_id = f"{row['work_id']}::{row['passage_id']}"
                    if bundle_id in seen_bundle_ids:
                        continue
                    translation = await _fetch_translation_for_passage(ctx.deps, str(row["passage_id"]))
                    if translation:
                        translation_pairs.append(
                            {
                                "original_passage_id": str(row["passage_id"]),
                                "translation_passage_id": str(translation.get("passage_id"))
                                if translation.get("passage_id")
                                else None,
                                "translation_node_id": translation.get("kg_node_id"),
                                "section_path": section.get("path"),
                            }
                        )
                    original_text = row.get("text_content") or ""
                    translation_text = translation.get("text_content") if translation else None
                    bundle = EvidenceBundle(
                        bundle_id=bundle_id,
                        work_id=str(row["work_id"]),
                        work_title=row.get("title", ""),
                        author=row.get("author"),
                        section_path=section.get("path", ""),
                        canonical_ref=row.get("canonical_ref"),
                        original_passage_id=str(row["passage_id"]),
                        translation_passage_id=(
                            str(translation["passage_id"])
                            if translation and translation.get("passage_id")
                            else None
                        ),
                        original_text=original_text,
                        translation_text=translation_text,
                        language=row.get("language"),
                        token_estimate=RetrievalBudget.estimate_tokens(
                            "\n".join(
                                part
                                for part in (original_text, translation_text)
                                if part
                            )
                        ),
                        evidence_role="primary_support",
                        source=EvidenceSource.TREE_REASONING,
                        metadata={
                            "sequence_number": row.get("sequence_number"),
                            "translation_available": bool(translation_text),
                            "translation_source": translation.get("source") if translation else None,
                            "translation_node_id": translation.get("kg_node_id") if translation else None,
                        },
                    )
                    bundles.append(bundle)
                    seen_bundle_ids.add(bundle_id)

        if translation_pairs:
            _record_tool_call(
                state,
                tool_name="fetch_translation_pair",
                stage_id="evidence_bundles",
                rationale="pair original-language passages with their linked translations",
                selected_ids=[
                    item["translation_passage_id"] or item["translation_node_id"]
                    for item in translation_pairs[:20]
                    if item["translation_passage_id"] or item["translation_node_id"]
                ],
                details={
                    "pair_count": len(translation_pairs),
                    "pairs": translation_pairs[:12],
                },
            )

        supplemental = await _supplemental_passage_bundles(ctx, bundles, seen_bundle_ids)
        if supplemental:
            _record_tool_call(
                state,
                tool_name="read_passage_bundle",
                stage_id="evidence_bundles",
                rationale="supplement tree-selected evidence with directly linked high-value passages",
                selected_ids=[bundle.bundle_id for bundle in supplemental[:16]],
                details={"supplemental_count": len(supplemental)},
            )
        bundles.extend(supplemental)

        state.evidence_bundles.extend(bundles)
        for bundle in state.evidence_bundles:
            bundle.metadata.update(
                {
                    key: value
                    for key, value in _bundle_academic_features(bundle, state).items()
                    if value not in (None, False, "", [])
                }
            )
        state.passages_used = len(state.evidence_bundles)
        notebook = _ensure_notebook(state)
        for bundle in bundles:
            notebook.reading_notes.append(
                ReadingNote(
                    note_id=bundle.bundle_id,
                    thesis=f"{bundle.work_title} contributes direct textual evidence.",
                    work_id=bundle.work_id,
                    section_path=bundle.section_path,
                    evidence_ids=[bundle.bundle_id],
                )
            )
        _build_scholarly_dossier(state)
        state.context_pack = _build_context_pack(state)
        state.accumulated_context = state.context_pack.prompt_context
        if bundles:
            _record_reading_decision(
                state,
                stage_id="evidence_bundles",
                decision_type="bundle_acceptance",
                title="Accept evidence bundles into the dossier",
                rationale="Bundles are retained when they add direct text, testimony, or counter-evidence for the active facets.",
                selected_ids=[bundle.bundle_id for bundle in bundles[:20]],
                supporting_refs=[
                    state.context_pack.bundle_refs.get(bundle.bundle_id, bundle.bundle_id)
                    for bundle in bundles[:12]
                    if state.context_pack.bundle_refs.get(bundle.bundle_id)
                ],
                metadata={
                    "bundle_count": len(bundles),
                    "work_titles": list(dict.fromkeys(bundle.work_title for bundle in bundles[:12])),
                },
            )
        _trace_stage(
            state,
            "evidence_bundles",
            {
                "bundle_count": len(state.evidence_bundles),
                "bundle_sample": [
                    {
                        "bundle_id": bundle.bundle_id,
                        "work_title": bundle.work_title,
                        "author": bundle.author,
                        "source": bundle.source.value,
                        "canonical_ref": bundle.canonical_ref,
                        "translation_source": bundle.metadata.get("translation_source"),
                    }
                    for bundle in state.evidence_bundles[:20]
                ],
            },
        )
        return SeekCounterEvidence()


@dataclass
class SeekCounterEvidence(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Mark bundles that complicate the main hypotheses."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> EvidenceSufficiency:
        state = ctx.state
        notebook = _ensure_notebook(state)
        if _should_minimize_llm_calls(state) or not state.evidence_bundles or not notebook.competing_hypotheses:
            _trace_stage(
                state,
                "counter_evidence",
                {
                    "mode": "skipped",
                    "selected_count": 0,
                    "rationale": "minimal-llm mode or insufficient bundles",
                    "bundle_ids": [],
                },
            )
            return EvidenceSufficiency()

        payload = [
            _bundle_prompt_dict(
                bundle,
                state.context_pack.bundle_refs.get(bundle.bundle_id, bundle.bundle_id),
            )
            for bundle in state.context_pack.passage_bundles[:20]
        ]
        try:
            raw = await ctx.deps.llm.generate(
                COUNTER_EVIDENCE_PROMPT.format(
                    question_frame=notebook.question_frame or state.question,
                    hypotheses="\n".join(f"- {item}" for item in notebook.competing_hypotheses[:4]),
                    bundles_json=truncate_json(payload, 9000),
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=600,
                thinking_mode=True,
                cache_key="counter-evidence",
                cache_prefix="counter_evidence_v1",
            )
            parsed = CounterEvidenceResult.model_validate(_parse_json(raw))
            selected = set(parsed.bundle_ids)
            rationale = parsed.rationale
            mode = "llm"
        except Exception:
            selected = {
                bundle.bundle_id
                for bundle in state.evidence_bundles[1:3]
                if bundle.author != state.evidence_bundles[0].author
            }
            rationale = "heuristic author divergence"
            mode = "heuristic"

        if selected:
            for bundle in state.evidence_bundles:
                if bundle.bundle_id in selected:
                    bundle.evidence_role = "counter_evidence"
                    bundle.metadata["evidence_class"] = "counter_evidence"
            notebook.counter_evidence.append(rationale)
            _build_scholarly_dossier(state)
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context
            _record_reading_decision(
                state,
                stage_id="counter_evidence",
                decision_type="counter_evidence_selection",
                title="Mark counter-evidence bundles",
                rationale=rationale,
                selected_ids=sorted(selected)[:12],
                supporting_refs=[
                    state.context_pack.bundle_refs.get(bundle_id, bundle_id)
                    for bundle_id in sorted(selected)[:12]
                    if state.context_pack.bundle_refs.get(bundle_id)
                ],
            )
        _trace_stage(
            state,
            "counter_evidence",
            {
                "mode": mode,
                "selected_count": len(selected),
                "bundle_ids": sorted(selected)[:8],
                "rationale": rationale,
            },
        )
        return EvidenceSufficiency()


@dataclass
class EvidenceSufficiency(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Single sufficiency gate after bundle expansion."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> DraftClaimLedger | DiscoverCorpus:
        state = ctx.state
        notebook = _ensure_notebook(state)
        bundle_count = len(state.context_pack.passage_bundles)
        work_count = len({bundle.work_id for bundle in state.context_pack.passage_bundles})
        counter_count = len(notebook.counter_evidence)
        dossier = state.scholarly_dossier if state.scholarly_dossier.facets else _build_scholarly_dossier(state)
        covered_facets = sum(
            1
            for facet in dossier.facets
            if facet.primary_bundle_ids or facet.testimony_bundle_ids or facet.metadata_ids
        )
        heuristic_score = min(
            1.0,
            0.12 * bundle_count + 0.08 * work_count + 0.1 * counter_count + 0.08 * covered_facets,
        )
        if _should_minimize_llm_calls(state):
            score = heuristic_score
            sufficient = score >= 0.45
            reason = "heuristic sufficiency (minimal llm mode)"
            refinement = None
        else:
            try:
                raw = await ctx.deps.llm.generate(
                    SUFFICIENCY_PROMPT.format(
                        question=state.question,
                        bundle_count=bundle_count,
                        work_count=work_count,
                        counter_count=counter_count,
                        open_questions=", ".join(notebook.open_questions[:5]) or "(none)",
                    ),
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.0,
                    max_tokens=256,
                    cache_key="evidence-sufficiency",
                    cache_prefix="evidence_sufficiency_v1",
                )
                assessment = SufficiencyAssessment.model_validate(_parse_json(raw))
                score = max(heuristic_score, assessment.score)
                sufficient = assessment.sufficient
                reason = assessment.reason
                refinement = assessment.refinement
            except Exception:
                score = heuristic_score
                sufficient = score >= 0.45
                reason = "heuristic sufficiency"
                refinement = None

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

        if (
            not sufficient
            and state.iteration < 1
            and state.pipeline_config.use_tree_reasoning
            and refinement
        ):
            state.iteration += 1
            state.sub_queries = [refinement]
            notebook.uncertainties.append(reason)
            _record_reading_decision(
                state,
                stage_id="evidence_sufficiency",
                decision_type="refine_search",
                title="Refine the corpus search",
                rationale=reason,
                selected_ids=[refinement],
                metadata={"score": round(score, 4)},
            )
            return DiscoverCorpus()

        if not sufficient:
            notebook.uncertainties.append(reason)
        return DraftClaimLedger()


@dataclass
class DraftClaimLedger(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Draft a structured claim ledger before prose generation."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> RenderGroundedAnswer:
        state = ctx.state
        notebook = _ensure_notebook(state)
        if not state.context_pack.prompt_context:
            state.context_pack = _build_context_pack(state)
            state.accumulated_context = state.context_pack.prompt_context
        dossier = _build_scholarly_dossier(state)
        default_facet_id = next(
            (
                facet.facet_id
                for facet in dossier.facets
                if "textual" in facet.title.lower() or "definition" in facet.title.lower()
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
                    evidence_class=_bundle_academic_features(direct_quote_bundle, state)["evidence_class"],
                    quote_original=truncate_text(direct_quote_bundle.original_text, 1400),
                    quote_translation=truncate_text(direct_quote_bundle.translation_text, 1400)
                    if direct_quote_bundle.translation_text
                    else None,
                    support_type="passage",
                    confidence=1.0,
                    status=ClaimStatus.SUPPORTED,
                )
            ]
            notebook.claim_ledger = state.claim_ledger
            state.metadata["claim_ledger_mode"] = "deterministic_quote"
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
            raw = await ctx.deps.llm.generate(
                CLAIM_LEDGER_PROMPT.format(
                    question=state.question,
                    grounding_policy=state.grounding_policy.value,
                    notebook_json=truncate_json(notebook.model_dump(), 12000),
                    dossier_json=truncate_json(_scholarly_dossier_payload(state), 16000),
                    evidence_catalog_json=truncate_json(evidence_catalog, 12000),
                    context=truncate_text(state.context_pack.prompt_context, 30000),
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=3800,
                response_mime_type="application/json",
                response_json_schema=CLAIM_LEDGER_RESPONSE_SCHEMA,
                cache_key="claim-ledger",
                cache_prefix="claim_ledger_v2",
            )
            parsed = _coerce_claim_ledger_payload(_parse_json(raw))
            valid_ids = set(state.context_pack.bundle_refs) | set(state.context_pack.node_refs)
            claims = [
                ClaimLedgerItem(
                    claim=item.claim,
                    evidence_ids=_resolve_claim_evidence_ids(
                        [str(eid) for eid in item.evidence_ids],
                        item.support_type,
                        state,
                    ),
                    facet_id=item.facet_id or default_facet_id,
                    evidence_class=item.evidence_class or ("metadata" if item.support_type == "metadata" else "direct_text"),
                    quote_original=item.quote_original,
                    quote_translation=item.quote_translation,
                    support_type=_normalize_claim_support_type(item.support_type),
                    confidence=item.confidence,
                    status=item.status,
                )
                for item in parsed.claims
                if item.claim
            ]
            claims = [item for item in claims if any(eid in valid_ids for eid in item.evidence_ids)]
            claims = _augment_claim_ledger_from_dossier(state, claims)
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
            claims = []
            salvaged = _salvage_claim_ledger(raw) if raw else None
            if salvaged is not None:
                valid_ids = set(state.context_pack.bundle_refs) | set(state.context_pack.node_refs)
                claims = [
                    ClaimLedgerItem(
                        claim=item.claim,
                        evidence_ids=_resolve_claim_evidence_ids(
                            [str(eid) for eid in item.evidence_ids],
                            item.support_type,
                            state,
                        ),
                        facet_id=item.facet_id or default_facet_id,
                        evidence_class=item.evidence_class or ("metadata" if item.support_type == "metadata" else "direct_text"),
                        quote_original=item.quote_original,
                        quote_translation=item.quote_translation,
                        support_type=_normalize_claim_support_type(item.support_type),
                        confidence=item.confidence,
                        status=item.status,
                    )
                    for item in salvaged.claims
                    if item.claim
                ]
                claims = [item for item in claims if any(eid in valid_ids for eid in item.evidence_ids)]
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
        state.claim_ledger = claims
        notebook.claim_ledger = claims
        _update_insufficiency_flags_from_claims(state)
        return RenderGroundedAnswer()


@dataclass
class RenderGroundedAnswer(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Render prose from the claim ledger using stable prompt caching."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> ProgrammaticVerify:
        state = ctx.state
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
                lines.append(f'English translation: "{quote_item.quote_translation}" [{ref}]')
            state.raw_answer = "\n".join(lines).strip()
            state.metadata["render_answer_mode"] = "deterministic_quote"
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": "deterministic_quote",
                    "raw_excerpt": truncate_text(state.raw_answer, 2000),
                },
            )
            return ProgrammaticVerify()

        reference_map = {
            item.claim: _claim_reference_markers(state, item)
            for item in state.claim_ledger
        }
        evidence_packet = _render_evidence_packet(state)
        requirements = _render_requirements(state)

        raw_answer = ""
        try:
            raw_answer = await ctx.deps.llm.generate(
                RENDER_ANSWER_PROMPT.format(
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
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=3200,
                cache_key="render-grounded-answer",
                cache_prefix="render_grounded_answer_v2",
            )
            rendered_answer = raw_answer.strip()
            if rendered_answer and not _should_minimize_llm_calls(state):
                try:
                    polished_answer = await ctx.deps.llm.generate(
                        SCHOLARLY_POLISH_PROMPT.format(
                            question=state.question,
                            dossier_json=truncate_json(dossier_payload, 14000),
                            draft_answer=truncate_text(rendered_answer, 18000),
                        ),
                        system_prompt=SYSTEM_PROMPT,
                        temperature=0.1,
                        max_tokens=3200,
                        cache_key="scholarly-polish",
                        cache_prefix="scholarly_polish_v2",
                    )
                    polished_answer = polished_answer.strip()
                    if polished_answer:
                        rendered_answer = polished_answer
                        state.metadata["scholarly_polish_mode"] = "llm"
                        _trace_stage(
                            state,
                            "scholarly_polish",
                            {
                                "mode": "llm",
                                "raw_excerpt": truncate_text(polished_answer, 2000),
                            },
                        )
                except Exception as exc:
                    state.metadata["scholarly_polish_mode"] = "fallback"
                    _trace_stage(
                        state,
                        "scholarly_polish",
                        {
                            "mode": "fallback",
                            "error": f"{type(exc).__name__}: {exc}",
                        },
                    )
            compression_repair_mode = "skipped"
            if rendered_answer and not _should_minimize_llm_calls(state) and _answer_is_too_compressed(state, rendered_answer):
                try:
                    repaired_answer = await ctx.deps.llm.generate(
                        COMPRESSION_REPAIR_PROMPT.format(
                            question=state.question,
                            required_sections=requirements["required_sections"],
                            required_quote_blocks=requirements["required_quote_blocks"],
                            facet_titles="\n".join(
                                f"- {facet.title}" for facet in _supported_dossier_facets(state)
                            ) or "- General answer",
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
                    )
                    repaired_answer = repaired_answer.strip()
                    if repaired_answer:
                        rendered_answer = repaired_answer
                        compression_repair_mode = "llm"
                except Exception:
                    compression_repair_mode = "fallback"
                    logger.warning("Compression repair failed", exc_info=True)
            state.metadata["compression_repair_mode"] = compression_repair_mode

            fallback_answer = _render_answer_fallback(state)
            if not rendered_answer or _answer_is_too_compressed(state, rendered_answer):
                rendered_answer = fallback_answer
            state.raw_answer = rendered_answer
            fallback_used = state.raw_answer == fallback_answer
            state.metadata["render_answer_mode"] = "fallback" if fallback_used else "llm"
            if fallback_used:
                state.metadata["pipeline_degraded"] = True
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": state.metadata["render_answer_mode"],
                    "raw_excerpt": truncate_text(state.raw_answer, 2000),
                    "polish_mode": state.metadata.get("scholarly_polish_mode", "skipped"),
                    "compression_repair_mode": compression_repair_mode,
                    "render_requirements": requirements,
                    "shape_metrics": _answer_shape_metrics(state.raw_answer),
                },
            )
        except Exception as exc:
            state.raw_answer = _render_answer_fallback(state)
            state.metadata["render_answer_mode"] = "fallback"
            state.metadata["pipeline_degraded"] = True
            _trace_stage(
                state,
                "render_grounded_answer",
                {
                    "mode": "fallback",
                    "error": f"{type(exc).__name__}: {exc}",
                    "raw_excerpt": truncate_text(raw_answer, 2000) if raw_answer else "",
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
        answer, citations = _verify_answer_programmatically(state)
        state.raw_answer = answer
        state.citations = citations
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
        state.self_rag_evaluation = SelfRAGEvaluation(
            relevance=score,
            grounding=100 if citations else 25,
            completeness=score,
            confidence=score,
            caveats=state.research_notebook.uncertainties[:3],
            improvements=[],
        )
        state.metadata["research_graph"] = _build_research_graph_payload(state)
        return End(_make_answer(state))


# ---------------------------------------------------------------------------
# Legacy compatibility wrappers
# ---------------------------------------------------------------------------


@dataclass
class DirectKGLookup(DiscoverCorpus):
    """Compatibility alias for the old direct-lookup node."""


@dataclass
class HybridRetrieve(DiscoverCorpus):
    """Compatibility alias for the old hybrid-retrieval node."""


@dataclass
class DecomposeQuery(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that seeds sub-queries before discovery."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> SearchPrimarySources:
        state = ctx.state
        if not state.sub_queries:
            state.sub_queries = [state.expanded_query or state.question]
        return SearchPrimarySources()


@dataclass
class SearchPrimarySources(DiscoverCorpus):
    """Compatibility alias for the old primary-source search node."""


@dataclass
class EvaluateSufficiency(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that routes into the new notebook/tree flow."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> TreeNavigateWorks:
        await _build_research_frame(ctx)
        return TreeNavigateWorks()


@dataclass
class SearchSecondarySources(SeekCounterEvidence):
    """Compatibility alias mapping to counter-evidence search."""


@dataclass
class TreeReasoningRetrieve(TreeNavigateWorks):
    """Compatibility alias for old tree-reasoning node."""


@dataclass
class CRAGValidate(EvidenceSufficiency):
    """Compatibility alias for the new single sufficiency gate."""


@dataclass
class DualRerank(ExpandEvidenceBundles):
    """Compatibility alias; bundle expansion subsumes reranking pressure."""


@dataclass
class FetchPassagesAndLayer(ExpandEvidenceBundles):
    """Compatibility alias for bundle expansion and context packing."""


@dataclass
class Synthesize(DraftClaimLedger):
    """Compatibility alias for claim-ledger drafting."""


@dataclass
class SynthesizeWithHierarchy(DraftClaimLedger):
    """Compatibility alias for hierarchical claim-ledger drafting."""


@dataclass
class VerifyCitations(ProgrammaticVerify):
    """Compatibility alias for programmatic verification."""


@dataclass
class SelfRAGEvaluate(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper returning the final answer immediately."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> End[ScholarlyAnswer]:
        if not ctx.state.citations and ctx.state.raw_answer:
            answer, citations = _verify_answer_programmatically(ctx.state)
            ctx.state.raw_answer = answer
            ctx.state.citations = citations
        ctx.state.quality_badge = _quality_badge_from_state(ctx.state)
        return End(_make_answer(ctx.state))


@dataclass
class RefineSynthesis(BaseNode[RAGState, Deps, ScholarlyAnswer]):
    """Compatibility wrapper that re-renders from the ledger."""

    async def run(
        self,
        ctx: GraphRunContext[RAGState, Deps],
    ) -> VerifyCitations:
        ctx.state.self_rag_iterations += 1
        ctx.state.raw_answer = _render_answer_fallback(ctx.state)
        return VerifyCitations()
