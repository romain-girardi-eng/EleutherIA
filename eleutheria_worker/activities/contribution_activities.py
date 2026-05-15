"""Activities for ``ProcessContributionWorkflow`` (Feature 8 — PDF
ingestion of community KG contributions).

The pipeline turns a single uploaded PDF (``free_will.kg_contributions`` row)
into structured KG proposals:

1. ``extract_pdf_text``    — pull text + structural metadata from the PDF
2. ``classify_relevance``  — score the article for free-will relevance
3. ``extract_kg_proposals``— extract scholar / passage / edge proposals
4. ``persist_*``           — write everything back into Postgres

Every public function in this module is a plain ``async def`` so the same
implementation can run from:

* the Temporal worker (via the ``@activity.defn`` wrappers at the bottom)
* the synchronous fallback runner in ``backend.services.contribution_pipeline``
* the operator CLI in ``database/scripts/process_contribution_cli.py``

The activities themselves are **pure functions of their arguments** — they
receive concrete ``DatabaseService`` / ``LLMService`` instances rather than
constructing their own, so they're trivially mockable in tests.
"""

from __future__ import annotations

import io
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid hard runtime deps on backend/graphrag in the worker
    from eleutheria_database.services.db import DatabaseService
    from eleutheria_graphrag.services.llm_service import LLMService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tunables — exported so tests can monkey-patch
# ---------------------------------------------------------------------------

RELEVANCE_THRESHOLD = 0.4
"""Minimum score before stage 3 (proposal extraction) runs."""

CLASSIFY_TEXT_BUDGET = 30_000
"""Characters of full_text fed into the relevance classifier."""

EXTRACT_TEXT_BUDGET = 60_000
"""Characters of full_text fed into each of the three proposal sub-extractors."""

PROPOSAL_MODEL = "accounts/fireworks/ai/models/kimi-k2.6-instruct"
"""Default Fireworks model id for tool-calling. Callers can override."""

EXISTING_NODE_SIMILARITY_MIN = 0.65
"""``similarity()`` threshold for surfacing potential KG matches."""

EXISTING_NODE_SIMILARITY_STRONG = 0.85
"""Above this we collapse a 'new node' proposal into an existing match."""


# ---------------------------------------------------------------------------
# Dataclasses (also serve as the activity I/O envelopes)
# ---------------------------------------------------------------------------


@dataclass
class PdfPage:
    page_no: int
    text: str
    blocks: list[str] = field(default_factory=list)


@dataclass
class StructuredMetadata:
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    doi: str | None = None
    publication_year: int | None = None
    abstract: str | None = None


@dataclass
class ExtractedPdf:
    pages: list[PdfPage]
    structured_metadata: StructuredMetadata
    full_text: str


@dataclass
class RelevanceResult:
    score: float
    summary: str
    concepts: list[str]


@dataclass
class Proposal:
    """A single row destined for ``kg_contribution_proposals``."""

    kind: str  # node | edge | passage_citation | scholar_ref | concept_attestation
    payload: dict[str, Any]
    target_kg_id: str | None = None
    confidence: float = 0.5
    evidence: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stage 1 — PDF extraction
# ---------------------------------------------------------------------------


_TITLE_LINE_MIN_LEN = 10
_TITLE_LINE_MAX_LEN = 200
_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_AUTHOR_PREFIX_RE = re.compile(r"\b(dr|prof|professor|mr|ms|mrs)\.?\b", re.IGNORECASE)
_ABSTRACT_HEAD_RE = re.compile(r"\bABSTRACT\b\s*[:\-]?\s*", re.IGNORECASE)
_ABSTRACT_MAX = 1500


async def download_pdf(pdf_url: str) -> bytes:
    """Fetch the PDF bytes.

    Accepts either:

    * an HTTP(S) URL (Supabase Storage signed URL or public link)
    * a filesystem path (used by the CLI for manual reruns)
    """
    if pdf_url.startswith(("http://", "https://")):
        import httpx

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            return resp.content
    path = Path(pdf_url)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_url}")
    return path.read_bytes()


def _extract_pages_pypdf(pdf_bytes: bytes) -> list[PdfPage]:
    """Extract pages via ``pypdf``. Returns raw text per page."""
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    out: list[PdfPage] = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 — bad pages shouldn't kill the whole run
            logger.exception("pypdf failed on page %d", idx)
            text = ""
        # Block heuristic: split on double newlines, keep non-empty runs
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        out.append(PdfPage(page_no=idx, text=text, blocks=blocks))
    return out


def _looks_like_title(line: str) -> bool:
    stripped = line.strip()
    if not (_TITLE_LINE_MIN_LEN <= len(stripped) <= _TITLE_LINE_MAX_LEN):
        return False
    letters = [c for c in stripped if c.isalpha()]
    if not letters:
        return False
    # Reject ALL CAPS headers (journal banners, running heads).
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio > 0.9:
        return False
    # Reject obvious DOI / page-number lines.
    return not (
        _DOI_RE.search(stripped) or stripped.lower().startswith(("doi", "page "))
    )


def _parse_title(first_page_text: str) -> str | None:
    for raw in first_page_text.splitlines():
        if _looks_like_title(raw):
            return raw.strip()
    return None


def _parse_authors(first_page_text: str, title: str | None) -> list[str]:
    lines = [ln.strip() for ln in first_page_text.splitlines() if ln.strip()]
    if not lines:
        return []
    start = 0
    if title:
        for i, ln in enumerate(lines):
            if ln == title:
                start = i + 1
                break
    # Take up to 3 lines after the title, stop at the first paragraph break /
    # abstract heading.
    candidate_lines: list[str] = []
    for ln in lines[start : start + 5]:
        if _ABSTRACT_HEAD_RE.search(ln):
            break
        if len(ln) > 200:
            break
        candidate_lines.append(ln)

    joined = " and ".join(candidate_lines)
    # Strip prefixes, split on commas / 'and' / '&' / semicolons.
    cleaned = _AUTHOR_PREFIX_RE.sub("", joined)
    pieces = re.split(r"\s*(?:,|\band\b|&|;)\s*", cleaned, flags=re.IGNORECASE)
    authors: list[str] = []
    for raw in pieces:
        name = raw.strip(" .,")
        # Heuristic: real names have at least two tokens and < 6.
        tokens = name.split()
        if 2 <= len(tokens) <= 6 and all(t[:1].isalpha() for t in tokens):
            authors.append(name)
    # Dedupe preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for a in authors:
        key = a.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)
    return deduped


def _parse_doi(text: str) -> str | None:
    m = _DOI_RE.search(text)
    return m.group(0).rstrip(".,;)") if m else None


def _parse_year(text: str, doi: str | None) -> int | None:
    # Prefer a year sitting next to the DOI / journal block.
    candidates: list[int] = []
    if doi:
        window = text[max(0, text.find(doi) - 400) : text.find(doi) + 400]
        candidates.extend(int(m.group(0)) for m in _YEAR_RE.finditer(window))
    candidates.extend(int(m.group(0)) for m in _YEAR_RE.finditer(text[:3000]))
    # Keep plausible publication years.
    candidates = [y for y in candidates if 1900 <= y <= 2099]
    if not candidates:
        return None
    # Pick the most common — banner years repeat across pages.
    from collections import Counter

    return Counter(candidates).most_common(1)[0][0]


def _parse_abstract(pages: list[PdfPage]) -> str | None:
    for page in pages[:2]:
        m = _ABSTRACT_HEAD_RE.search(page.text)
        if not m:
            continue
        tail = page.text[m.end() :].lstrip()
        # Stop at the next double newline OR at the first heading-style line.
        paragraph = re.split(r"\n\s*\n", tail, maxsplit=1)[0].strip()
        if paragraph:
            return paragraph[:_ABSTRACT_MAX]
    return None


def _build_structured_metadata(pages: list[PdfPage]) -> StructuredMetadata:
    if not pages:
        return StructuredMetadata()
    first = pages[0].text
    title = _parse_title(first)
    authors = _parse_authors(first, title)
    head_text = "\n".join(p.text for p in pages[:3])
    doi = _parse_doi(head_text)
    year = _parse_year(head_text, doi)
    abstract = _parse_abstract(pages)
    return StructuredMetadata(
        title=title,
        authors=authors,
        doi=doi,
        publication_year=year,
        abstract=abstract,
    )


async def extract_pdf_text(pdf_url: str) -> ExtractedPdf:
    """Stage 1: download the PDF and extract text + structural metadata.

    Pure async function — safe to call from any context.
    """
    pdf_bytes = await download_pdf(pdf_url)
    pages = _extract_pages_pypdf(pdf_bytes)
    if not pages:
        raise RuntimeError(f"No text extracted from PDF at {pdf_url}")
    metadata = _build_structured_metadata(pages)
    full_text = "\n\n".join(p.text for p in pages)
    return ExtractedPdf(
        pages=pages,
        structured_metadata=metadata,
        full_text=full_text,
    )


# ---------------------------------------------------------------------------
# Stage 2 — Free-will relevance classification
# ---------------------------------------------------------------------------


RELEVANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "summary": {"type": "string"},
        "concepts": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["score", "summary", "concepts"],
    "additionalProperties": False,
}


RELEVANCE_PROMPT = """You are an expert in ancient + early Christian + medieval philosophy and the history of the free-will debate. You are evaluating whether a scholarly article is relevant to a research platform focused on free will, fate, moral responsibility, αὐτεξούσιον, prohairesis, libertarianism, compatibilism, fatalism, providence, predestination, akrasia, the Lazy Argument, the Master Argument, the Sea Battle.

ARTICLE METADATA:
Title: {title}
Authors: {authors}
Abstract: {abstract}

ARTICLE TEXT (truncated):
{truncated_text}

Return ONLY valid JSON matching this schema:
{{
  "score": 0.0,
  "summary": "...",
  "concepts": [ ... ]
}}

Where:
- score: 0.0 = not relevant at all, 1.0 = central to the free-will debate
- summary: 2-3 sentences explaining the article's stance / contribution
- concepts: canonical concept ids from this list when applicable: autexousion, prohairesis, to_eph_hemin, heimarmene, providence, predestination, akrasia, libertarianism, compatibilism, fatalism, sea_battle, lazy_argument, master_argument, cylinder_analogy, swerve, sympatheia, ekpyrosis, synkatathesis. Add new concept names freely if needed; ALL lowercase snake_case.
"""


def _coerce_relevance(raw: str) -> RelevanceResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Defend against models that wrap JSON in markdown fences.
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        data = json.loads(cleaned)
    score = float(data.get("score", 0.0))
    score = max(0.0, min(1.0, score))
    summary = str(data.get("summary", "")).strip()
    concepts_raw = data.get("concepts") or []
    concepts = [str(c).strip().lower() for c in concepts_raw if str(c).strip()]
    return RelevanceResult(score=score, summary=summary, concepts=concepts)


async def classify_relevance(
    extracted: ExtractedPdf,
    llm: LLMService,
    *,
    model_override: str | None = None,
) -> RelevanceResult:
    """Stage 2: ask the LLM to score free-will relevance."""
    md = extracted.structured_metadata
    prompt = RELEVANCE_PROMPT.format(
        title=md.title or "(unknown)",
        authors=", ".join(md.authors) or "(unknown)",
        abstract=md.abstract or "(no abstract found)",
        truncated_text=extracted.full_text[:CLASSIFY_TEXT_BUDGET],
    )
    raw = await llm.generate(
        prompt=prompt,
        temperature=0.1,
        max_tokens=1024,
        response_json_schema=RELEVANCE_SCHEMA,
        model_override=model_override,
    )
    return _coerce_relevance(raw)


# ---------------------------------------------------------------------------
# Stage 3 — KG proposal extraction
# ---------------------------------------------------------------------------


SCHOLAR_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "submit_scholars",
        "description": (
            "Submit modern scholars and ancient persons/schools discussed in the article."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node_type": {
                                "type": "string",
                                "enum": ["scholar", "person", "school"],
                            },
                            "label": {"type": "string"},
                            "proposed_id": {"type": "string"},
                            "description": {"type": "string"},
                            "period": {"type": "string"},
                            "evidence_page": {"type": "integer"},
                            "evidence_excerpt": {"type": "string"},
                        },
                        "required": ["node_type", "label", "proposed_id"],
                    },
                }
            },
            "required": ["proposals"],
        },
    },
}


CITATION_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "submit_citations",
        "description": "Submit ancient quotes / references attested in the article.",
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "citation_text": {"type": "string"},
                            "ancient_text": {"type": "string"},
                            "translation": {"type": "string"},
                            "scholar_node_id": {"type": "string"},
                            "stance": {
                                "type": "string",
                                "enum": [
                                    "supports",
                                    "critiques",
                                    "discusses",
                                    "explicates",
                                ],
                            },
                            "evidence_page": {"type": "integer"},
                            "evidence_excerpt": {"type": "string"},
                        },
                        "required": ["citation_text"],
                    },
                }
            },
            "required": ["proposals"],
        },
    },
}


EDGE_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "submit_edges",
        "description": (
            "Submit interpretive edges between scholars and KG entities "
            "(concepts, arguments, persons)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "proposals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject_id": {"type": "string"},
                            "predicate": {
                                "type": "string",
                                "enum": [
                                    "interprets",
                                    "critiques",
                                    "supports",
                                    "introduces",
                                    "rejects",
                                ],
                            },
                            "object_id": {"type": "string"},
                            "claim": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence_page": {"type": "integer"},
                            "evidence_excerpt": {"type": "string"},
                        },
                        "required": [
                            "subject_id",
                            "predicate",
                            "object_id",
                            "claim",
                        ],
                    },
                }
            },
            "required": ["proposals"],
        },
    },
}


def _extractor_messages(
    extracted: ExtractedPdf,
    relevance: RelevanceResult,
    instructions: str,
) -> list[dict[str, Any]]:
    md = extracted.structured_metadata
    user = (
        f"Article title: {md.title or '(unknown)'}\n"
        f"Authors: {', '.join(md.authors) or '(unknown)'}\n"
        f"Abstract: {md.abstract or '(no abstract)'}\n"
        f"Relevance score: {relevance.score:.2f}\n"
        f"Relevance summary: {relevance.summary}\n\n"
        f"ARTICLE TEXT (truncated):\n{extracted.full_text[:EXTRACT_TEXT_BUDGET]}"
    )
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user},
    ]


async def _call_tool(
    llm: LLMService,
    messages: list[dict[str, Any]],
    tool: dict[str, Any],
    *,
    model_override: str | None,
) -> list[dict[str, Any]]:
    """Force a single tool-call and return its ``proposals`` array."""
    tool_name = tool["function"]["name"]
    msg = await llm.generate_with_tools(
        messages=messages,
        tools=[tool],
        tool_choice={"type": "function", "function": {"name": tool_name}},
        temperature=0.1,
        max_tokens=2048,
        model_override=model_override,
    )
    calls = msg.get("tool_calls") or []
    if not calls:
        logger.warning("Extractor returned no tool_calls for %s", tool_name)
        return []
    raw_args = calls[0].get("function", {}).get("arguments", "{}")
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except json.JSONDecodeError:
        logger.exception("Bad JSON in tool_call for %s: %r", tool_name, raw_args)
        return []
    proposals = args.get("proposals") or []
    return [p for p in proposals if isinstance(p, dict)]


SCHOLAR_SYSTEM = (
    "You extract structured KG nodes from scholarly philosophy articles. "
    "Identify EVERY named modern scholar referenced or critiqued in the article, "
    "and EVERY ancient person or school discussed. For each, propose a node "
    "with a snake_case `proposed_id` of the form `scholar_<lastname>_<initial>` "
    "or `person_<name>_<century>`. Set `period` to one of: Presocratic, "
    "Classical, Hellenistic, Imperial, Late Antiquity, Patristic, Medieval, "
    "Renaissance, Modern."
)


CITATION_SYSTEM = (
    "You extract attested ancient citations from scholarly articles. Identify "
    "every ancient work reference, quotation in Greek/Latin, or named passage. "
    "`citation_text` is the canonical reference (e.g. 'Nic. Eth. III.5', "
    "'1 Apol. 43', 'De Fato §28'). When the original ancient text is quoted, "
    "capture it verbatim in `ancient_text` (preserve all diacritics). When "
    "a translation appears, capture it in `translation`. `scholar_node_id` is "
    "the snake_case id of the modern scholar making the citation, when known."
)


EDGE_SYSTEM = (
    "You extract interpretive claims from scholarly articles, expressed as "
    "edges between a modern scholar (subject) and a KG entity (object: "
    "concept, argument, or ancient person). Use `predicate` ∈ {interprets, "
    "critiques, supports, introduces, rejects}. For `object_id` prefer "
    "canonical KG ids when known (e.g. `concept_autexousion`, "
    "`person_chrysippus`), otherwise reference a `proposed_id` from the "
    "scholars/persons step. `confidence` ∈ [0, 1]."
)


async def _extract_scholars(
    extracted: ExtractedPdf,
    relevance: RelevanceResult,
    llm: LLMService,
    *,
    model_override: str | None,
) -> list[dict[str, Any]]:
    messages = _extractor_messages(extracted, relevance, SCHOLAR_SYSTEM)
    return await _call_tool(llm, messages, SCHOLAR_TOOL, model_override=model_override)


async def _extract_citations(
    extracted: ExtractedPdf,
    relevance: RelevanceResult,
    llm: LLMService,
    *,
    model_override: str | None,
) -> list[dict[str, Any]]:
    messages = _extractor_messages(extracted, relevance, CITATION_SYSTEM)
    return await _call_tool(llm, messages, CITATION_TOOL, model_override=model_override)


async def _extract_edges(
    extracted: ExtractedPdf,
    relevance: RelevanceResult,
    llm: LLMService,
    *,
    model_override: str | None,
) -> list[dict[str, Any]]:
    messages = _extractor_messages(extracted, relevance, EDGE_SYSTEM)
    return await _call_tool(llm, messages, EDGE_TOOL, model_override=model_override)


# ---------- KG lookups (existing-node matching + edge resolution) ----------


async def _find_similar_nodes(db: DatabaseService, label: str) -> list[dict[str, Any]]:
    """Return top-3 fuzzy matches against ``kg_nodes.label`` via pg_trgm."""
    rows = await db.fetch(
        """
        SELECT node_id AS id, label, similarity(label, $1) AS sim
        FROM free_will.kg_nodes
        WHERE similarity(label, $1) > $2
        ORDER BY sim DESC
        LIMIT 3
        """,
        label,
        EXISTING_NODE_SIMILARITY_MIN,
    )
    return list(rows)


async def _node_exists(db: DatabaseService, node_id: str) -> bool:
    val = await db.fetchval(
        "SELECT 1 FROM free_will.kg_nodes WHERE node_id = $1 LIMIT 1",
        node_id,
    )
    return val is not None


async def _find_passage_match(db: DatabaseService, citation_text: str) -> str | None:
    """Best-effort passage match against ``passages.canonical_ref``."""
    if not citation_text:
        return None
    row = await db.fetchrow(
        """
        SELECT passage_id::text AS passage_id
        FROM free_will.passages
        WHERE canonical_ref ILIKE $1
        ORDER BY length(canonical_ref) ASC
        LIMIT 1
        """,
        f"%{citation_text.strip()}%",
    )
    return row["passage_id"] if row else None


# ---------- Proposal assembly ----------


async def _scholar_to_proposal(raw: dict[str, Any], db: DatabaseService) -> Proposal:
    label = str(raw.get("label", "")).strip()
    matches = await _find_similar_nodes(db, label) if label else []
    matches_existing_id: str | None = None
    if matches and matches[0]["sim"] >= EXISTING_NODE_SIMILARITY_STRONG:
        matches_existing_id = matches[0]["id"]
    payload = {
        "node_type": raw.get("node_type", "scholar"),
        "label": label,
        "proposed_id": raw.get("proposed_id"),
        "matches_existing_id": matches_existing_id,
        "description": raw.get("description"),
        "period": raw.get("period"),
        "candidate_matches": [
            {"id": m["id"], "label": m["label"], "sim": float(m["sim"])}
            for m in matches
        ],
        "evidence_page": raw.get("evidence_page"),
        "evidence_excerpt": raw.get("evidence_excerpt"),
    }
    return Proposal(
        kind="node",
        payload=payload,
        target_kg_id=matches_existing_id,
        confidence=0.9 if matches_existing_id else 0.6,
        evidence={
            "page": raw.get("evidence_page"),
            "excerpt": raw.get("evidence_excerpt"),
        },
    )


async def _citation_to_proposal(raw: dict[str, Any], db: DatabaseService) -> Proposal:
    citation_text = str(raw.get("citation_text", "")).strip()
    matched = await _find_passage_match(db, citation_text)
    payload = {
        "citation_text": citation_text,
        "ancient_text": raw.get("ancient_text"),
        "translation": raw.get("translation"),
        "matched_passage_id": matched,
        "scholar_node_id": raw.get("scholar_node_id"),
        "stance": raw.get("stance"),
        "evidence_page": raw.get("evidence_page"),
        "evidence_excerpt": raw.get("evidence_excerpt"),
    }
    return Proposal(
        kind="passage_citation",
        payload=payload,
        target_kg_id=matched,
        confidence=0.85 if matched else 0.5,
        evidence={
            "page": raw.get("evidence_page"),
            "excerpt": raw.get("evidence_excerpt"),
        },
    )


async def _edge_to_proposal(
    raw: dict[str, Any],
    db: DatabaseService,
    proposed_ids: set[str],
) -> Proposal:
    subject_id = str(raw.get("subject_id", "")).strip()
    object_id = str(raw.get("object_id", "")).strip()
    subj_exists = await _node_exists(db, subject_id) if subject_id else False
    obj_exists = await _node_exists(db, object_id) if object_id else False

    subj_proposed = subject_id in proposed_ids and not subj_exists
    obj_proposed = object_id in proposed_ids and not obj_exists

    payload = {
        "subject_id": subject_id,
        "predicate": raw.get("predicate"),
        "object_id": object_id,
        "claim": raw.get("claim"),
        "confidence": float(raw.get("confidence", 0.5)),
        "subject_resolution": (
            "existing" if subj_exists else "proposed" if subj_proposed else "unresolved"
        ),
        "object_resolution": (
            "existing" if obj_exists else "proposed" if obj_proposed else "unresolved"
        ),
        "evidence_page": raw.get("evidence_page"),
        "evidence_excerpt": raw.get("evidence_excerpt"),
    }
    return Proposal(
        kind="edge",
        payload=payload,
        target_kg_id=None,
        confidence=float(raw.get("confidence", 0.5)),
        evidence={
            "page": raw.get("evidence_page"),
            "excerpt": raw.get("evidence_excerpt"),
        },
    )


async def extract_kg_proposals(
    extracted: ExtractedPdf,
    relevance: RelevanceResult,
    db: DatabaseService,
    llm: LLMService,
    *,
    model_override: str | None = None,
) -> list[Proposal]:
    """Stage 3: run the three LLM sub-calls and assemble Proposal rows."""
    target_model = model_override or PROPOSAL_MODEL

    scholars_raw = await _extract_scholars(
        extracted, relevance, llm, model_override=target_model
    )
    citations_raw = await _extract_citations(
        extracted, relevance, llm, model_override=target_model
    )
    edges_raw = await _extract_edges(
        extracted, relevance, llm, model_override=target_model
    )

    proposals: list[Proposal] = []
    proposed_ids: set[str] = set()
    for raw in scholars_raw:
        prop = await _scholar_to_proposal(raw, db)
        proposals.append(prop)
        pid = prop.payload.get("proposed_id")
        if isinstance(pid, str) and pid:
            proposed_ids.add(pid)

    for raw in citations_raw:
        proposals.append(await _citation_to_proposal(raw, db))

    for raw in edges_raw:
        proposals.append(await _edge_to_proposal(raw, db, proposed_ids))

    return proposals


# ---------------------------------------------------------------------------
# Stage 4 — Persistence
# ---------------------------------------------------------------------------


async def load_contribution(
    db: DatabaseService, contribution_id: str
) -> dict[str, Any]:
    """Fetch the contribution row; raises if it doesn't exist."""
    row = await db.fetchrow(
        """
        SELECT contribution_id::text AS contribution_id,
               pdf_url,
               pdf_filename,
               status
        FROM free_will.kg_contributions
        WHERE contribution_id = $1::uuid
        """,
        contribution_id,
    )
    if row is None:
        raise LookupError(f"No kg_contributions row for {contribution_id}")
    return dict(row)


async def mark_processing(db: DatabaseService, contribution_id: str) -> None:
    await db.execute(
        """
        UPDATE free_will.kg_contributions
        SET status = 'processing',
            processing_error = NULL
        WHERE contribution_id = $1::uuid
        """,
        contribution_id,
    )


async def persist_low_relevance(
    db: DatabaseService,
    contribution_id: str,
    metadata: StructuredMetadata,
    relevance: RelevanceResult,
) -> None:
    """Write metadata + score and mark the contribution 'ready' (no proposals)."""
    await db.execute(
        """
        UPDATE free_will.kg_contributions
        SET status            = 'ready',
            title             = COALESCE($2, title),
            authors            = $3,
            doi                = COALESCE($4, doi),
            publication_year   = COALESCE($5, publication_year),
            pdf_metadata       = $6::jsonb,
            relevance_score    = $7,
            relevance_summary  = $8,
            free_will_concepts = $9,
            processing_error   = NULL
        WHERE contribution_id = $1::uuid
        """,
        contribution_id,
        metadata.title,
        metadata.authors,
        metadata.doi,
        metadata.publication_year,
        json.dumps(_metadata_to_jsonb(metadata)),
        relevance.score,
        relevance.summary,
        relevance.concepts,
    )


async def persist_proposals(
    db: DatabaseService,
    contribution_id: str,
    metadata: StructuredMetadata,
    relevance: RelevanceResult,
    proposals: list[Proposal],
) -> None:
    """Update the contribution row + bulk-insert all proposals."""
    await db.execute(
        """
        UPDATE free_will.kg_contributions
        SET status             = 'ready',
            title              = COALESCE($2, title),
            authors             = $3,
            doi                 = COALESCE($4, doi),
            publication_year    = COALESCE($5, publication_year),
            pdf_metadata        = $6::jsonb,
            relevance_score     = $7,
            relevance_summary   = $8,
            free_will_concepts  = $9,
            processing_error    = NULL
        WHERE contribution_id = $1::uuid
        """,
        contribution_id,
        metadata.title,
        metadata.authors,
        metadata.doi,
        metadata.publication_year,
        json.dumps(_metadata_to_jsonb(metadata)),
        relevance.score,
        relevance.summary,
        relevance.concepts,
    )

    for prop in proposals:
        await db.execute(
            """
            INSERT INTO free_will.kg_contribution_proposals
                (contribution_id, kind, payload, target_kg_id, confidence, evidence)
            VALUES ($1::uuid, $2, $3::jsonb, $4, $5, $6::jsonb)
            """,
            contribution_id,
            prop.kind,
            json.dumps(prop.payload),
            prop.target_kg_id,
            prop.confidence,
            json.dumps(prop.evidence),
        )


async def mark_failed(db: DatabaseService, contribution_id: str, error: str) -> None:
    await db.execute(
        """
        UPDATE free_will.kg_contributions
        SET status = 'failed',
            processing_error = $2
        WHERE contribution_id = $1::uuid
        """,
        contribution_id,
        error[:4000],
    )


def _metadata_to_jsonb(metadata: StructuredMetadata) -> dict[str, Any]:
    """Serialise StructuredMetadata for the ``pdf_metadata`` jsonb column."""
    return {
        "title": metadata.title,
        "authors": metadata.authors,
        "doi": metadata.doi,
        "publication_year": metadata.publication_year,
        "abstract": metadata.abstract,
    }


# ---------------------------------------------------------------------------
# Temporal activity wrappers
#
# The activities only depend on a contribution_id at the workflow boundary —
# the DatabaseService and LLMService are constructed fresh inside the worker
# from environment variables. Pure-function arguments (ExtractedPdf,
# RelevanceResult) are passed through verbatim so workflow replay stays
# deterministic.
# ---------------------------------------------------------------------------


def _build_db_from_env() -> DatabaseService:
    """Build a per-activity DatabaseService.

    Imports are local because the worker module must stay importable from
    contexts where backend/graphrag aren't on the path.
    """
    from eleutheria_database.services.db import DatabaseService

    return DatabaseService()


def _build_llm_from_env() -> LLMService:
    from eleutheria_graphrag.services.llm_service import LLMService

    return LLMService()


try:
    from temporalio import activity
except ImportError:  # pragma: no cover — temporalio is a dev/worker-time dep
    activity = None  # type: ignore[assignment]


if activity is not None:

    @activity.defn(name="extract_pdf_text")
    async def extract_pdf_text_activity(contribution_id: str) -> dict[str, Any]:
        """Activity wrapper: fetches the pdf_url and returns a JSON-friendly
        payload that survives Temporal serialization."""
        activity.logger.info(f"extract_pdf_text: {contribution_id}")
        db = _build_db_from_env()
        await db.connect()
        try:
            row = await load_contribution(db, contribution_id)
            await mark_processing(db, contribution_id)
        finally:
            await db.close()
        extracted = await extract_pdf_text(row["pdf_url"])
        return _extracted_to_dict(extracted)

    @activity.defn(name="classify_relevance")
    async def classify_relevance_activity(
        extracted_payload: dict[str, Any],
    ) -> dict[str, Any]:
        activity.logger.info("classify_relevance")
        extracted = _extracted_from_dict(extracted_payload)
        llm = _build_llm_from_env()
        relevance = await classify_relevance(extracted, llm)
        return {
            "score": relevance.score,
            "summary": relevance.summary,
            "concepts": relevance.concepts,
        }

    @activity.defn(name="extract_kg_proposals")
    async def extract_kg_proposals_activity(
        extracted_payload: dict[str, Any],
        relevance_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        activity.logger.info("extract_kg_proposals")
        extracted = _extracted_from_dict(extracted_payload)
        relevance = RelevanceResult(**relevance_payload)
        db = _build_db_from_env()
        llm = _build_llm_from_env()
        await db.connect()
        try:
            props = await extract_kg_proposals(extracted, relevance, db, llm)
        finally:
            await db.close()
        return [_proposal_to_dict(p) for p in props]

    @activity.defn(name="persist_low_relevance")
    async def persist_low_relevance_activity(
        contribution_id: str,
        extracted_payload: dict[str, Any],
        relevance_payload: dict[str, Any],
    ) -> None:
        activity.logger.info(f"persist_low_relevance: {contribution_id}")
        extracted = _extracted_from_dict(extracted_payload)
        relevance = RelevanceResult(**relevance_payload)
        db = _build_db_from_env()
        await db.connect()
        try:
            await persist_low_relevance(
                db,
                contribution_id,
                extracted.structured_metadata,
                relevance,
            )
        finally:
            await db.close()

    @activity.defn(name="persist_proposals")
    async def persist_proposals_activity(
        contribution_id: str,
        extracted_payload: dict[str, Any],
        relevance_payload: dict[str, Any],
        proposals_payload: list[dict[str, Any]],
    ) -> None:
        activity.logger.info(
            f"persist_proposals: {contribution_id} ({len(proposals_payload)} proposals)"
        )
        extracted = _extracted_from_dict(extracted_payload)
        relevance = RelevanceResult(**relevance_payload)
        proposals = [_proposal_from_dict(p) for p in proposals_payload]
        db = _build_db_from_env()
        await db.connect()
        try:
            await persist_proposals(
                db,
                contribution_id,
                extracted.structured_metadata,
                relevance,
                proposals,
            )
        finally:
            await db.close()

    @activity.defn(name="mark_contribution_failed")
    async def mark_failed_activity(contribution_id: str, error: str) -> None:
        activity.logger.warning(f"mark_failed: {contribution_id}: {error[:200]}")
        db = _build_db_from_env()
        await db.connect()
        try:
            await mark_failed(db, contribution_id, error)
        finally:
            await db.close()


# ---------------------------------------------------------------------------
# (De)serialization helpers — exported for the workflow + sync runner.
# ---------------------------------------------------------------------------


def _extracted_to_dict(extracted: ExtractedPdf) -> dict[str, Any]:
    return {
        "pages": [
            {"page_no": p.page_no, "text": p.text, "blocks": p.blocks}
            for p in extracted.pages
        ],
        "structured_metadata": {
            "title": extracted.structured_metadata.title,
            "authors": extracted.structured_metadata.authors,
            "doi": extracted.structured_metadata.doi,
            "publication_year": extracted.structured_metadata.publication_year,
            "abstract": extracted.structured_metadata.abstract,
        },
        "full_text": extracted.full_text,
    }


def _extracted_from_dict(payload: dict[str, Any]) -> ExtractedPdf:
    pages = [
        PdfPage(
            page_no=int(p["page_no"]),
            text=str(p.get("text", "")),
            blocks=list(p.get("blocks") or []),
        )
        for p in payload.get("pages") or []
    ]
    md_raw = payload.get("structured_metadata") or {}
    metadata = StructuredMetadata(
        title=md_raw.get("title"),
        authors=list(md_raw.get("authors") or []),
        doi=md_raw.get("doi"),
        publication_year=md_raw.get("publication_year"),
        abstract=md_raw.get("abstract"),
    )
    return ExtractedPdf(
        pages=pages,
        structured_metadata=metadata,
        full_text=str(payload.get("full_text", "")),
    )


def _proposal_to_dict(prop: Proposal) -> dict[str, Any]:
    return {
        "kind": prop.kind,
        "payload": prop.payload,
        "target_kg_id": prop.target_kg_id,
        "confidence": prop.confidence,
        "evidence": prop.evidence,
    }


def _proposal_from_dict(payload: dict[str, Any]) -> Proposal:
    return Proposal(
        kind=str(payload["kind"]),
        payload=dict(payload.get("payload") or {}),
        target_kg_id=payload.get("target_kg_id"),
        confidence=float(payload.get("confidence", 0.5)),
        evidence=dict(payload.get("evidence") or {}),
    )
